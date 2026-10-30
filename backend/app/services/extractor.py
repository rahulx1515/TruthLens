"""
TruthLens - URL News Extraction Service
Implements safe, SSRF-resistant news article extraction using Trafilatura and BeautifulSoup.
"""
import ipaddress
import socket
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
import trafilatura
from app.core.config import settings


class ExtractionError(Exception):
    """Custom exception for URL extraction failures."""
    pass


def is_ip_private_or_internal(ip_str: str) -> bool:
    """Checks if an IP address falls into private, loopback, link-local, or reserved ranges."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private or
            ip.is_loopback or
            ip.is_link_local or
            ip.is_multicast or
            ip.is_reserved or
            ip.is_unspecified
        )
    except ValueError:
        return True


def validate_url_safety(url_str: str):
    """
    Validates URL safety and guards against Server-Side Request Forgery (SSRF).
    - Checks HTTP/HTTPS scheme
    - Resolves host DNS and validates resolved IPs against private/internal CIDR blocks
    """
    if not url_str or not isinstance(url_str, str):
        raise ExtractionError("A valid URL string must be provided.")

    parsed = urlparse(url_str)
    if parsed.scheme.lower() not in ("http", "https"):
        raise ExtractionError(f"Unsupported URL scheme '{parsed.scheme}'. Only http and https are permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise ExtractionError("URL has no valid hostname.")

    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        raise ExtractionError("Access to internal hostnames is prohibited.")

    # If hostname is already an IP literal, validate immediately without DNS query
    try:
        ip = ipaddress.ip_address(hostname)
        if is_ip_private_or_internal(str(ip)):
            raise ExtractionError(f"Access to private/internal IP address '{hostname}' is blocked for security.")
        return
    except ValueError:
        pass

    # Resolve hostname to IPv4/IPv6 and verify not private
    try:
        addr_info = socket.getaddrinfo(hostname, None)
        for entry in addr_info:
            sockaddr = entry[4]
            ip_str = sockaddr[0]
            if is_ip_private_or_internal(ip_str):
                raise ExtractionError(f"Access to private/internal IP address '{ip_str}' is blocked for security.")
    except socket.gaierror:
        raise ExtractionError(f"Could not resolve hostname '{hostname}'. Please verify the web address.")


def extract_article_from_url(url: str) -> dict:
    """
    Safely fetches and extracts clean title, body text, domain, and author from a news URL.
    Enforces SSRF prevention, revalidates DNS and redirects on EVERY hop,
    strictly enforces response size limits and timeouts.
    """
    current_url = url
    max_redirects = 5
    redirect_count = 0

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36 TruthLens/2.0"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
    }

    raw_html = ""
    final_url = current_url

    try:
        with httpx.Client(timeout=settings.REQUEST_TIMEOUT_SECONDS, follow_redirects=False) as client:
            while redirect_count <= max_redirects:
                # Revalidate safety before EVERY hop
                validate_url_safety(current_url)

                with client.stream("GET", current_url, headers=headers) as response:
                    # Check for redirect status codes
                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get("location")
                        if not location:
                            raise ExtractionError("Redirect missing Location header.")
                        # Handle relative redirects
                        from urllib.parse import urljoin
                        current_url = urljoin(current_url, location)
                        redirect_count += 1
                        continue

                    if response.status_code in (401, 403):
                        raise ExtractionError("Access denied by the website (paywalled or restricted).")
                    if response.status_code >= 400:
                        raise ExtractionError(f"Website responded with HTTP status error {response.status_code}.")

                    content_type = response.headers.get("content-type", "").lower()
                    if "text/html" not in content_type and "application/xhtml" not in content_type:
                        raise ExtractionError("Target URL does not return an HTML web page.")

                    # Read up to MAX_RESPONSE_SIZE_BYTES
                    chunks = []
                    total_bytes = 0
                    for chunk in response.iter_bytes():
                        total_bytes += len(chunk)
                        if total_bytes > settings.MAX_RESPONSE_SIZE_BYTES:
                            raise ExtractionError(
                                f"Response size exceeded the limit ({settings.MAX_RESPONSE_SIZE_BYTES / (1024*1024):.1f}MB)."
                            )
                        chunks.append(chunk)

                    raw_html = b"".join(chunks).decode("utf-8", errors="replace")
                    final_url = current_url
                    break
            else:
                raise ExtractionError("Too many redirects encountered while fetching article.")

    except httpx.TimeoutException:
        raise ExtractionError("Connection timed out while fetching article. The website may be slow or unavailable.")
    except httpx.RequestError as e:
        raise ExtractionError(f"Network error while connecting to website: {str(e)}")

    # 1. Primary Extraction: Trafilatura (state-of-the-art news extractor)
    extracted_text = trafilatura.extract(
        raw_html,
        include_comments=False,
        include_tables=False,
        no_fallback=False
    )
    metadata = trafilatura.extract_metadata(raw_html)

    title = ""
    author = None
    date = None

    if metadata:
        title = metadata.title or ""
        author = metadata.author
        date = metadata.date

    # 2. Fallback to BeautifulSoup if title or text is missing
    if not title or not extracted_text:
        soup = BeautifulSoup(raw_html, "html.parser")
        if not title:
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = og_title["content"]
            elif soup.title and soup.title.string:
                title = soup.title.string.strip()

        if not extracted_text:
            paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 20]
            extracted_text = "\n\n".join(paragraphs)

    if not extracted_text or len(extracted_text.strip()) < 50:
        raise ExtractionError("Could not extract substantial article text from the provided webpage.")

    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    return {
        "title": title.strip() if title else "Extracted Article",
        "text": extracted_text.strip(),
        "url": url,
        "domain": domain,
        "author": author,
        "published_date": date
    }
