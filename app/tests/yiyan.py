import os
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from aiohttp import web, ClientSession
from aiohttp.web import Request, Response

# Store API key in environment variable
API_KEY = os.environ.get("API_KEY", "")

async def handle_request(request: Request) -> Response:
    url = str(request.url)
    parsed_url = urlparse(url)
    pathname = parsed_url.path

    # Basic endpoints
    if pathname == "/":
        return Response(text="Linux.do proxy is running!", status=200)
    
    if pathname == "/robots.txt":
        return Response(text="User-agent: *\nDisallow: /", status=200)

    # Check if the path is for linux.do
    if pathname.startswith("/http://linux.do") or pathname.startswith("/https://linux.do"):
        try:
            # Extract target URL (remove leading slash)
            target_url = pathname[1:]
            
            # Copy query params except sensitive ones
            target_parsed = urlparse(target_url)
            query_params = parse_qs(parsed_url.query)
            
            # Filter out sensitive parameters
            filtered_params = {k: v for k, v in query_params.items() 
                             if k not in ["auth", "token", "key"]}
            
            # Reconstruct target URL with filtered params
            new_query = urlencode(filtered_params, doseq=True)
            target_url_final = urlunparse((
                target_parsed.scheme, target_parsed.netloc, target_parsed.path,
                target_parsed.params, new_query, target_parsed.fragment
            ))
            
            # Prepare headers
            headers = {}
            allowed_headers = ["accept", "content-type", "authorization", "user-agent"]
            
            for key, value in request.headers.items():
                if key.lower() in allowed_headers:
                    headers[key] = value
            
            # Add API key from environment variable
            if API_KEY:
                headers["User-Api-Key"] = API_KEY

            # Handle preflight requests
            if request.method == "OPTIONS":
                response_headers = {
                    "Access-Control-Allow-Origin": request.headers.get("Origin", "*"),
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": ", ".join(allowed_headers),
                    "X-Content-Type-Options": "nosniff"
                }
                return Response(status=204, headers=response_headers)

            # Make the request
            async with ClientSession() as session:
                body = await request.read() if request.can_read_body else None
                
                async with session.request(
                    method=request.method,
                    url=target_url_final,
                    headers=headers,
                    data=body
                ) as response:
                    
                    # Set CORS and security headers
                    response_headers = dict(response.headers)
                    response_headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
                    response_headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                    response_headers["Access-Control-Allow-Headers"] = ", ".join(allowed_headers)
                    response_headers["X-Content-Type-Options"] = "nosniff"

                    # Process HTML content to rewrite links
                    content_type = response_headers.get("content-type", "")
                    if "text/html" in content_type:
                        target_parsed_final = urlparse(target_url_final)
                        base_url = f"{target_parsed_final.scheme}://{target_parsed_final.netloc}"
                        text = await response.text()
                        
                        # Rewrite links and form actions
                        text = re.sub(
                            r'<form([^>]*)action="\/([^"]*)"([^>]*)>',
                            fr'<form\1action="/{base_url}/\2"\3>',
                            text
                        )
                        text = re.sub(
                            r'<form([^>]*)action="(https?:\/\/linux\.do[^"]*)"([^>]*)>',
                            r'<form\1action="/\2"\3>',
                            text
                        )
                        text = re.sub(
                            r'(href|src)="\/([^"]*)"',
                            fr'\1="/{base_url}/\2"',
                            text
                        )
                        text = re.sub(
                            r'(href|src)="(?!\/?https?:\/\/)([^"]*)"',
                            fr'\1="/{base_url}/\2"',
                            text
                        )
                        text = re.sub(
                            r'(href|src)="(https?:\/\/linux\.do[^"]*)"',
                            r'\1="/\2"',
                            text
                        )

                        return Response(
                            text=text, 
                            status=response.status, 
                            headers=response_headers
                        )

                    # Return non-HTML content as-is
                    content = await response.read()
                    return Response(
                        body=content, 
                        status=response.status, 
                        headers=response_headers
                    )

        except Exception as error:
            print(f"Proxy error: {error}")
            return Response(text="Proxy request failed", status=500)

    # Deny access to other domains
    return Response(text="Access denied. This proxy only supports linux.do", status=403)

def create_app():
    app = web.Application()
    app.router.add_route('*', '/{path:.*}', handle_request)
    return app

if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=8000)