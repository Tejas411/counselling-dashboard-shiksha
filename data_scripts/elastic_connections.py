import numpy as np
if not hasattr(np, 'float_'):
    np.float_ = np.float64

from elasticsearch import Elasticsearch

def get_es_client():
    host_ip = "10.20.74.114"
    port_num = 9200
    elasticsearch_client = Elasticsearch(
        [
            {
                'host': host_ip,
                'port': port_num,
                "scheme": "http"
            }
         ],
        timeout=1000)
   
    if elasticsearch_client.ping():
        print(f"Connection successful with the host: {host_ip}:{port_num}")
        return elasticsearch_client
    else:
        print(f"Connection Failed to {host_ip}:{port_num}")
        return None

if __name__ == "__main__":
    get_es_client()
