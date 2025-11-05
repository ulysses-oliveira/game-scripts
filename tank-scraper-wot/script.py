from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time


# ========== CONFIGURAÇÃO ==========
options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")

URL = "https://worldoftanks.com/pt-br/tankopedia/#wot&w_m=tanks&w_t=AT-SPG&w_l=11"


# ========== ETAPA 1 - LISTA DE TANQUES ==========
def tank_list(driver):
    driver.get(URL)
    time.sleep(5)  # Espera os tanques carregarem

    rows = driver.find_elements(By.CSS_SELECTOR, "a.table-view_row")

    basic_infos = []
    for row in rows:
        try:
            nome = row.find_element(By.CSS_SELECTOR, ".table-view_tank-name").text.strip()
            href = row.get_attribute("href")
            if href:
                tank_url = f"https://worldoftanks.com{href}" if href.startswith("/") else href
                basic_infos.append({
                    "nome": nome,
                    "url": tank_url
                })
        except Exception:
            continue

    print(f"🔎 {len(basic_infos)} tanques encontrados.")
    return basic_infos


# ========== ETAPA 2 - DADOS DE SOBREVIVÊNCIA ==========
def get_survivability_data(driver):
    """Extrai HP e blindagens (chassi + torre)."""
    spec_items = driver.find_elements(By.CSS_SELECTOR, ".specification_item")

    hp = None
    hull_armor = None
    turret_armor = None

    for item in spec_items:
        try:
            desc = item.find_element(By.CSS_SELECTOR, ".specification_description").text.strip()

            if "Pontos de Energia" in desc:
                hp = item.find_element(By.CSS_SELECTOR, ".specification_result span").text.strip()

            elif "Blindagem do Chassi" in desc:
                armor_text = item.find_element(By.CSS_SELECTOR, ".specification_result").text.strip()
                parts = armor_text.replace("mm", "").split("/")
                parts = [p.strip() for p in parts]
                hull_armor = {
                    "frontal": parts[0],
                    "lateral": parts[1],
                    "traseira": parts[2]
                }

            elif "Blindagem da Torre" in desc:
                armor_text = item.find_element(By.CSS_SELECTOR, ".specification_result").text.strip()
                parts = armor_text.replace("mm", "").split("/")
                parts = [p.strip() for p in parts]
                turret_armor = {
                    "frontal": parts[0],
                    "lateral": parts[1],
                    "traseira": parts[2]
                }

        except Exception:
            continue

    return {
        "HP": hp,
        "Blindagem Chassi (frontal)": hull_armor["frontal"] if hull_armor else None,
        "Blindagem Chassi (lateral)": hull_armor["lateral"] if hull_armor else None,
        "Blindagem Chassi (traseira)": hull_armor["traseira"] if hull_armor else None,
        "Blindagem Torre (frontal)": turret_armor["frontal"] if turret_armor else None,
        "Blindagem Torre (lateral)": turret_armor["lateral"] if turret_armor else None,
        "Blindagem Torre (traseira)": turret_armor["traseira"] if turret_armor else None
    }


# ========== ETAPA 3 - DADOS DE MOBILIDADE ==========
def get_mobility_data(driver):
    """Extrai velocidade máxima."""
    spec_items = driver.find_elements(By.CSS_SELECTOR, ".specification_item")

    speed = None

    for item in spec_items:
        try:
            desc = item.find_element(By.CSS_SELECTOR, ".specification_description").text.strip()

            if "Velocidade Máxima" in desc:
                speed = item.find_element(By.CSS_SELECTOR, ".specification_result span").text.strip()

        except Exception:
            continue

    return {
        "Velocidade": speed
    }


# ========== ETAPA 4 - DADOS DE PODER DE FOGO ==========
def get_firepower_data(driver):
    """Extrai dano, tempo de recarga e tempo de mira."""
    spec_items = driver.find_elements(By.CSS_SELECTOR, ".specification_item")

    damage = None
    reload_time = None
    aiming_time = None

    for item in spec_items:
        try:
            desc = item.find_element(By.CSS_SELECTOR, ".specification_description").text.strip()

            if desc == "Dano":
                damage_text = item.find_element(By.CSS_SELECTOR, ".specification_result").text.strip()
                damage = damage_text.replace("HP", "").split("/")[0].strip()


            elif "Tempo de recarga" in desc:
                reload_time = item.find_element(By.CSS_SELECTOR, ".specification_result span").text.strip()

            elif "Tempo de Mira" in desc:
                aiming_time = item.find_element(By.CSS_SELECTOR, ".specification_result span").text.strip()

        except Exception:
            continue

    return {
        "Dano": damage if damage else None,
        "Tempo de Recarga": reload_time,
        "Tempo de Mira": aiming_time
    }


# ========== ETAPA 5 - COLETA DETALHADA ==========
def tank_details(driver, tank_list):
    all_tanks = []

    for item in tank_list:
        try:
            print(f"🧩 Coletando: {item['nome']}")
            driver.get(item["url"])

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".specification_row"))
            )

            survivability = get_survivability_data(driver)
            mobility = get_mobility_data(driver)
            firepower = get_firepower_data(driver)

            all_tanks.append({
                "Nome": item["nome"],
                "URL": item["url"],
                **survivability,
                **mobility,
                **firepower
            })

        except Exception as e:
            print(f"❌ Erro ao processar {item['nome']}: {e}")
            continue

    return all_tanks


# ========== ETAPA 6 - EXECUÇÃO E SALVAMENTO ==========
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    tanks = tank_list(driver)
    results = tank_details(driver, tanks)
finally:
    driver.quit()

# Cria DataFrame
df = pd.DataFrame(results)

# Converte colunas numéricas
import re

def clean_number(value):
    """
    Limpa e converte strings numéricas tipo '2.000', '20', '35 mm' em inteiros.
    Mantém 2000, não 2.0.
    """
    if not value:
        return None
    
    # Remove tudo que não for número, vírgula, ponto
    value = re.sub(r"[^0-9,\.]", "", str(value))

    # Se o valor tiver ponto e for formato de milhar (ex: 2.000), remove o ponto
    # Só remove se o ponto for separador de milhar (ex: 2.000, 12.500)
    if re.match(r"^\d{1,3}(\.\d{3})+$", value):
        value = value.replace(".", "")
    
    # Troca vírgula decimal por ponto (caso tenha vírgula real, ex: 15,30)
    value = value.replace(",", ".")
    
    try:
        # Se não tiver ponto decimal, converte pra int
        return int(float(value)) if "." in value else int(value)
    except ValueError:
        return None


for col in df.columns:
    if any(x in col.lower() for x in ["hp", "blindagem", "recarga", "tempo", "dano", "velocidade"]):
        df[col] = df[col].apply(clean_number)

df.to_excel("tanques.xlsx", index=False)

print(f"✅ {len(df)} tanques salvos em 'tanques.xlsx'!")
