import os, re, requests, tls_client
from concurrent.futures import ThreadPoolExecutor
from typing import List, Set

PROXY = os.getenv('PROXY')
PROXIES = {
    'http': PROXY,
    'https': PROXY
}
OUTPUT_FILE = 'lista_numeros_spam.txt'

def fetch_url(url: str, use_proxy: bool = False, use_tls_client: bool = False) -> str:
    try:
        if use_tls_client:
            session = tls_client.Session(
                client_identifier="chrome138",
                random_tls_extension_order=True
            )
            if use_proxy:
                session.proxies = PROXIES
            response = session.get(url)
        else:
            response = requests.get(url, proxies=PROXIES if use_proxy else None, timeout=10)
            response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def extract_numbers_spamcalls(content: str) -> Set[str]:
    numbers = set()
    patterns = re.findall(r'[+346789]\d{8,11}', content)
    
    for num in patterns:
        if num.startswith('+34') and len(num[3:]) == 9:
            numbers.add(num[3:])
        elif num.startswith('34') and len(num[2:]) == 9:
            numbers.add(num[2:])
        elif len(num) == 9 and num[0] in '346789':
            numbers.add(num)
    
    return numbers

def extract_numbers_cleverdialer(content: str) -> Set[str]:
    numbers = set()
    patterns = re.findall(r'[6789]\d{8}', content)
    numbers.update(patterns)
    return numbers

def extract_numbers_generic(content: str) -> Set[str]:
    numbers = set()
    patterns = re.findall(r'[6789]\d{8}', content)
    numbers.update(patterns)
    return numbers

def process_spamcalls() -> Set[str]:
    url = "https://spamcalls.net/es/country-code/34"
    content = fetch_url(url)
    if not content:
        return set()
    return extract_numbers_spamcalls(content)

def process_cleverdialer() -> Set[str]:
    url = "https://www.cleverdialer.es/top-spammer-de-las-ultimas-24-horas"
    content = fetch_url(url)
    if not content:
        return set()
    return extract_numbers_cleverdialer(content)

def process_custom_paths(paths: List[str]) -> Set[str]:
    numbers = set()
    domains = [
        # (domain, use_proxy, use_tls_client)
        ("https://numerospam.es", False, False),
        ("https://www.listaspam.com", True, True)
    ]
    
    urls = []
    for path in paths:
        for domain, use_proxy, use_tls in domains:
            urls.append((f"{domain}{path}", use_proxy, use_tls))
    
    def fetch_and_extract(url_config):
        url, use_proxy, use_tls = url_config
        content = fetch_url(url, use_proxy, use_tls)
        if content:
            return extract_numbers_generic(content)
        return set()
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_and_extract, urls)
        for result in results:
            numbers.update(result)
    
    return numbers


def load_existing_numbers() -> Set[str]:
    try:
        with open(OUTPUT_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def save_numbers(new_numbers: Set[str]):
    existing_numbers = load_existing_numbers()
    combined_numbers = existing_numbers.union(new_numbers)
    
    with open(OUTPUT_FILE, 'w') as f:
        for num in sorted(combined_numbers):
            f.write(f"{num}\n")

def main():
    all_numbers = set()
    print("Processing spamcalls.net...")
    all_numbers.update(process_spamcalls())
    
    print("Processing cleverdialer.es...")
    all_numbers.update(process_cleverdialer())
    custom_paths = [
        "/prefijos/es/almeria",
        "/prefijos/es/huelva",
        "/prefijos/es/cadiz",
        "/prefijos/es/jaen",
        "/prefijos/es/cordoba",
        "/prefijos/es/malaga",
        "/prefijos/es/granada",
        "/prefijos/es/sevilla",
        "/prefijos/es/huesca",
        "/prefijos/es/teruel",
        "/prefijos/es/zaragoza",
        "/prefijos/es/asturias",
        "/prefijos/es/islas-baleares",
        "/prefijos/es/las-palmas",
        "/prefijos/es/santa-cruz-de-tenerife",
        "/prefijos/es/cantabria",
        "/prefijos/es/albacete",
        "/prefijos/es/ciudad-real",
        "/prefijos/es/cuenca",
        "/prefijos/es/guadalajara",
        "/prefijos/es/toledo",
        "/prefijos/es/avila",
        "/prefijos/es/burgos",
        "/prefijos/es/leon",
        "/prefijos/es/palencia",
        "/prefijos/es/salamanca",
        "/prefijos/es/segovia",
        "/prefijos/es/soria",
        "/prefijos/es/valladolid",
        "/prefijos/es/zamora",
        "/prefijos/es/barcelona",
        "/prefijos/es/girona",
        "/prefijos/es/lleida",
        "/prefijos/es/tarragona",
        "/prefijos/es/alicante",
        "/prefijos/es/castellon",
        "/prefijos/es/valencia",
        "/prefijos/es/badajoz",
        "/prefijos/es/caceres",
        "/prefijos/es/a-coruna",
        "/prefijos/es/lugo",
        "/prefijos/es/orense",
        "/prefijos/es/pontevedra",
        "/prefijos/es/alava",
        "/prefijos/es/vizcaya",
        "/prefijos/es/guipuzcoa",
        "/prefijos/es/la-rioja",
        "/prefijos/es/murcia",
        "/prefijos/es/madrid",
        "/prefijos/es/navarra",
        "/prefijos-especiales/es/704",
        "/prefijos-especiales/es/800",
        "/prefijos-especiales/es/803",
        "/prefijos-especiales/es/806",
        "/prefijos-especiales/es/807",
        "/prefijos-especiales/es/900",
        "/prefijos-especiales/es/901",
        "/prefijos-especiales/es/902",
        "/prefijos-especiales/es/903",
        "/prefijos-especiales/es/905",
        "/prefijos-especiales/es/906",
        "/prefijos-especiales/es/907",
        "/prefijos-especiales/es/908",
        "/prefijos-especiales/es/909",
        "/moviles/es/606",
        "/moviles/es/608",
        "/moviles/es/609",
        "/moviles/es/616",
        "/moviles/es/618",
        "/moviles/es/619",
        "/moviles/es/620",
        "/moviles/es/626",
        "/moviles/es/628",
        "/moviles/es/629",
        "/moviles/es/630",
        "/moviles/es/636",
        "/moviles/es/638",
        "/moviles/es/639",
        "/moviles/es/646",
        "/moviles/es/648",
        "/moviles/es/649",
        "/moviles/es/650",
        "/moviles/es/659",
        "/moviles/es/660",
        "/moviles/es/669",
        "/moviles/es/676",
        "/moviles/es/679",
        "/moviles/es/680",
        "/moviles/es/681",
        "/moviles/es/682",
        "/moviles/es/683",
        "/moviles/es/686",
        "/moviles/es/689",
        "/moviles/es/690",
        "/moviles/es/696",
        "/moviles/es/699",
        "/moviles/es/717",
        "/moviles/es/600",
        "/moviles/es/603",
        "/moviles/es/607",
        "/moviles/es/610",
        "/moviles/es/617",
        "/moviles/es/627",
        "/moviles/es/634",
        "/moviles/es/637",
        "/moviles/es/647",
        "/moviles/es/661",
        "/moviles/es/662",
        "/moviles/es/663",
        "/moviles/es/664",
        "/moviles/es/666",
        "/moviles/es/667",
        "/moviles/es/670",
        "/moviles/es/671",
        "/moviles/es/672",
        "/moviles/es/673",
        "/moviles/es/674",
        "/moviles/es/677",
        "/moviles/es/678",
        "/moviles/es/687",
        "/moviles/es/697",
        "/moviles/es/711",
        "/moviles/es/727",
        "/moviles/es/605",
        "/moviles/es/615",
        "/moviles/es/625",
        "/moviles/es/635",
        "/moviles/es/645",
        "/moviles/es/651",
        "/moviles/es/652",
        "/moviles/es/653",
        "/moviles/es/654",
        "/moviles/es/655",
        "/moviles/es/656",
        "/moviles/es/657",
        "/moviles/es/658",
        "/moviles/es/665",
        "/moviles/es/675",
        "/moviles/es/685",
        "/moviles/es/691",
        "/moviles/es/692",
        "/moviles/es/747",
        "/moviles/es/748",
        "/moviles/es/612",
        "/moviles/es/631",
        "/moviles/es/632",
        "/moviles/es/613",
        "/moviles/es/622",
        "/moviles/es/623",
        "/moviles/es/633",
        "/moviles/es/712",
        "/moviles/es/722",
        "/moviles/es/624",
        "/moviles/es/641",
        "/moviles/es/642",
        "/moviles/es/643",
        "/moviles/es/693",
        "/moviles/es/694",
        "/moviles/es/695",
        "/moviles/es/601",
        "/moviles/es/604",
        "/moviles/es/640",
        "/moviles/es/611",
        "/moviles/es/698",
        "/moviles/es/621",
        "/moviles/es/644",
        "/moviles/es/668",
        "/moviles/es/688",
        "/moviles/es/684",
        "/moviles/es/602",
        "/moviles/es/744"
    ]
    
    print("Processing custom paths...")
    all_numbers.update(process_custom_paths(custom_paths))
    final_numbers = {
        num for num in all_numbers 
        if len(num) == 9 and num[0] in '6789'
    }
    
    print(f"Found {len(final_numbers)} numbers")
    save_numbers(final_numbers)
    print(f"Numbers saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
