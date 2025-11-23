# app/backend/models.py
from typing import Optional
from pydantic import BaseModel, Field

class ProxyItem(BaseModel):
    ip: str = Field(..., description="IP address of the proxy server.")
    port: int = Field(..., gt=0, lt=65536, description="Port number of the proxy server.")
    protocol: str = Field(..., description="Protocol supported by the proxy (e.g., http, https, socks4, socks5).")
    country: Optional[str] = Field(None, description="Country of the proxy server.")
    anonymity: Optional[str] = Field(None, description="Anonymity level (e.g., elite, anonymous, transparent).")
    source: str = Field(..., description="Source from where the proxy was fetched.")
    
    # These fields are typically populated AFTER validation
    response_time: Optional[float] = Field(None, description="Response time of the proxy server in milliseconds.")
    last_checked: Optional[str] = Field(None, description="Timestamp of the last check for the proxy's availability.")
    is_valid: bool = Field(False, description="Indicates if the proxy is valid or not. Defaults to False.") # Changed default to False

    def proxy_string(self) -> str:
        return f"{self.protocol}://{self.ip}:{self.port}"

    # For de-duplication and dictionary keys
    def __hash__(self):
        return hash((self.ip, self.port, self.protocol))

    def __eq__(self, other):
        if not isinstance(other, ProxyItem):
            return NotImplemented
        return (self.ip, self.port, self.protocol) == (other.ip, other.port, other.protocol)