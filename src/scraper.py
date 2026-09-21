import os, re, httpx, tls_client
from concurrent.futures import ThreadPoolExecutor
from typing import List, Set

PROXY = os.getenv('PROXY')

OUTPUT_FILE = 'lista_numeros_spam.txt'

def fetch_url(url: str, use_proxy: bool = False, use_tls_client: bool = False) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "sec-ch-ua": "\"Google Chrome\";v=\"151\", \"Chromium\";v=\"151\", \"Not_A Brand\";v=\"99\"",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-ch-ua-mobile": "?0",
    }

    try:
        if use_tls_client:
            session = tls_client.Session(
                client_identifier="chrome_120",
                random_tls_extension_order=True
            )
            if use_proxy:
                session.proxy = PROXY
            response = session.get(url, headers=headers)
        else:
            response = httpx.get(url, headers=headers, proxy=PROXY if use_proxy else None, timeout=5)
            response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def fetch_urls_openspam() -> set:
    api_key = os.getenv("OPENSPAM_API_KEY")
    if not api_key:
        print("Error: OPENSPAM_API_KEY not set")
        return set()

    headers = {"X-API-Key": api_key}
    urls = [
        "https://api.openspam.es/api/top?limit=100",
        "https://api.openspam.es/api/recent?limit=100&horas=24",
    ]

    telefonos = set()

    for url in urls:
        try:
            response = httpx.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            payload = response.json()

            for numero in payload.get("data", {}).get("numeros", []) or []:
                telefono = numero.get("telefono")
                if telefono:
                    telefonos.add(telefono)

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            continue

    return telefonos


def extract_numbers_withprefix(content: str) -> Set[str]:
    numbers = set()
    
    numbers.update(re.findall(r'(?:\+34|34)?([6789]\d{8})', content))
    
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
    return extract_numbers_withprefix(content)

def process_tellows() -> Set[str]:
    url = "https://www.tellows.es/stats"
    content = fetch_url(url)
    if not content:
        return set()
    return extract_numbers_withprefix(content)

def process_cleverdialer() -> Set[str]:
    url = "https://www.cleverdialer.es/top-spammer-de-las-ultimas-24-horas"
    content = fetch_url(url)
    if not content:
        return set()
    return extract_numbers_generic(content)

def process_detectaspam() -> Set[str]:
    url = "https://detectaspam.com/"
    content = fetch_url(url)
    if not content:
        return set()
    return extract_numbers_generic(content)

def process_telefonospam() -> Set[str]:
    url = "https://www.telefonospam.com/ultimos"
    content = fetch_url(url)
    if not content:
        return set()
    return extract_numbers_generic(content)

def process_slickly() -> Set[str]:
    url = "https://slick.ly/es"
    content = fetch_url(url)
    if not content:
        return set()
    return extract_numbers_generic(content)

def process_datostelefonicos_last() -> Set[str]:
    url = "https://datostelefonicos.com/ultimos-buscados/es?limit=200"
    content = fetch_url(url)
    if not content:
        return set()
    return extract_numbers_generic(content)

def process_datostelefonicos_top() -> Set[str]:
    url = "https://datostelefonicos.com/mas-buscados/es?limit=200"
    content = fetch_url(url)
    if not content:
        return set()
    return extract_numbers_generic(content)

def process_openspam() -> Set[str]:
    # https://openspam.es/
    return {
        normalized
        for numero in fetch_urls_openspam()
        for normalized in extract_numbers_withprefix(numero)
    }

def process_quienes_last() -> Set[str]:
    url = "https://quienes.es/recientes"
    content = fetch_url(url)
    if not content:
        return set()
    return extract_numbers_generic(content)

def process_quienes_top() -> Set[str]:
    url = "https://quienes.es/"
    content = fetch_url(url)
    if not content:
        return set()
    return extract_numbers_generic(content)

def process_numerospam(paths: List[str]) -> Set[str]:
    numbers = set()
    domains = [
        # (domain, use_proxy, use_tls_client)
        ("https://numerospam.com", False, False),
        #("https://www.listaspam.com", True, True) # temp disabled; needs proxy
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

def process_listaspam(paths: List[str]) -> Set[str]:
    numbers = set()
    domains = [
        # (domain, use_proxy, use_tls_client)
        ("https://www.listaspam.com", False, True)
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

    all_numbers.update(process_spamcalls())
    all_numbers.update(process_cleverdialer())
    all_numbers.update(process_tellows())
    all_numbers.update(process_telefonospam())
    all_numbers.update(process_detectaspam())
    all_numbers.update(process_slickly())
    all_numbers.update(process_datostelefonicos_last())
    all_numbers.update(process_datostelefonicos_top())
    all_numbers.update(process_openspam())
    all_numbers.update(process_quienes_last())
    all_numbers.update(process_quienes_top())

    paths_listaspam = [
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

    
    paths_numerospam = [
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
        "/prefijos/es/baleares",
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
        "/prefijos/es/ourense",
        "/prefijos/es/pontevedra",
        "/prefijos/es/alava",
        "/prefijos/es/vizcaya",
        "/prefijos/es/guipuzcoa",
        "/prefijos/es/la-rioja",
        "/prefijos/es/murcia",
        "/prefijos/es/madrid",
        "/prefijos/es/navarra",
        "/especiales/800",
        "/especiales/803",
        "/especiales/806",
        "/especiales/807",
        "/especiales/900",
        "/especiales/901",
        "/especiales/902",
        "/especiales/905",
        "/prefijos/moviles/606",
        "/prefijos/moviles/608",
        "/prefijos/moviles/609",
        "/prefijos/moviles/616",
        "/prefijos/moviles/618",
        "/prefijos/moviles/619",
        "/prefijos/moviles/620",
        "/prefijos/moviles/626",
        "/prefijos/moviles/628",
        "/prefijos/moviles/629",
        "/prefijos/moviles/630",
        "/prefijos/moviles/636",
        "/prefijos/moviles/638",
        "/prefijos/moviles/639",
        "/prefijos/moviles/646",
        "/prefijos/moviles/648",
        "/prefijos/moviles/649",
        "/prefijos/moviles/650",
        "/prefijos/moviles/659",
        "/prefijos/moviles/660",
        "/prefijos/moviles/669",
        "/prefijos/moviles/676",
        "/prefijos/moviles/679",
        "/prefijos/moviles/680",
        "/prefijos/moviles/681",
        "/prefijos/moviles/682",
        "/prefijos/moviles/683",
        "/prefijos/moviles/686",
        "/prefijos/moviles/689",
        "/prefijos/moviles/690",
        "/prefijos/moviles/696",
        "/prefijos/moviles/699",
        "/prefijos/moviles/717",
        "/prefijos/moviles/600",
        "/prefijos/moviles/603",
        "/prefijos/moviles/607",
        "/prefijos/moviles/610",
        "/prefijos/moviles/617",
        "/prefijos/moviles/627",
        "/prefijos/moviles/634",
        "/prefijos/moviles/637",
        "/prefijos/moviles/647",
        "/prefijos/moviles/661",
        "/prefijos/moviles/662",
        "/prefijos/moviles/663",
        "/prefijos/moviles/664",
        "/prefijos/moviles/666",
        "/prefijos/moviles/667",
        "/prefijos/moviles/670",
        "/prefijos/moviles/671",
        "/prefijos/moviles/672",
        "/prefijos/moviles/673",
        "/prefijos/moviles/674",
        "/prefijos/moviles/677",
        "/prefijos/moviles/678",
        "/prefijos/moviles/687",
        "/prefijos/moviles/697",
        "/prefijos/moviles/711",
        "/prefijos/moviles/727",
        "/prefijos/moviles/605",
        "/prefijos/moviles/615",
        "/prefijos/moviles/625",
        "/prefijos/moviles/635",
        "/prefijos/moviles/645",
        "/prefijos/moviles/651",
        "/prefijos/moviles/652",
        "/prefijos/moviles/653",
        "/prefijos/moviles/654",
        "/prefijos/moviles/655",
        "/prefijos/moviles/656",
        "/prefijos/moviles/657",
        "/prefijos/moviles/658",
        "/prefijos/moviles/665",
        "/prefijos/moviles/675",
        "/prefijos/moviles/685",
        "/prefijos/moviles/691",
        "/prefijos/moviles/692",
        "/prefijos/moviles/747",
        "/prefijos/moviles/748",
        "/prefijos/moviles/612",
        "/prefijos/moviles/631",
        "/prefijos/moviles/632",
        "/prefijos/moviles/613",
        "/prefijos/moviles/622",
        "/prefijos/moviles/623",
        "/prefijos/moviles/633",
        "/prefijos/moviles/712",
        "/prefijos/moviles/722",
        "/prefijos/moviles/624",
        "/prefijos/moviles/641",
        "/prefijos/moviles/642",
        "/prefijos/moviles/643",
        "/prefijos/moviles/693",
        "/prefijos/moviles/694",
        "/prefijos/moviles/695",
        "/prefijos/moviles/601",
        "/prefijos/moviles/604",
        "/prefijos/moviles/640",
        "/prefijos/moviles/611",
        "/prefijos/moviles/698",
        "/prefijos/moviles/621",
        "/prefijos/moviles/644",
        "/prefijos/moviles/668",
        "/prefijos/moviles/688",
        "/prefijos/moviles/684",
        "/prefijos/moviles/602",
        "/prefijos/moviles/744"
    ]
    
    all_numbers.update(process_numerospam(paths_numerospam))
    all_numbers.update(process_listaspam(paths_listaspam))
    
    final_numbers = {
        num for num in all_numbers 
        if len(num) == 9 and num[0] in '6789'
    }
    print(f"Found {len(final_numbers)} numbers")
    save_numbers(final_numbers)
    print(f"Numbers saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
