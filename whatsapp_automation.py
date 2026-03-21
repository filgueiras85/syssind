import pandas as pd
import time
import pyperclip
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==================== CONFIGURAÇÕES ====================
EXCEL_FILE = "aliexpress.xlsx"
# Abas solicitadas pelo usuário
SHEETS = ['Planilha14','Planilha15','Planilha16','Planilha17','Planilha18','Planilha19','Planilha20','Planilha21']

# Delays baseados no seu arquivo base (ali-meli.py) e solicitações anteriores
DELAY_SEARCH = 5
DELAY_AFTER_OPEN_CHAT = 5
DELAY_AFTER_LINK = 10
DELAY_BETWEEN_MESSAGES = 8

# ==================== FUNÇÕES AUXILIARES ====================

def encontrar_campo_busca(wait, driver):
    """
    Localiza o campo de busca e garante que ele esteja interagível,
    usando JavaScript como fallback para versões novas do WhatsApp Web.
    """
    seletores = [
        'input[data-tab="3"]',
        'input[aria-label="Pesquisar ou começar uma nova conversa"]',
        'input[placeholder="Pesquisar ou começar uma nova conversa"]',
        'input[role="textbox"]',
        'div[contenteditable="true"][data-tab="3"]' # Adicionado como fallback extra
    ]

    elemento = None
    for seletor in seletores:
        try:
            elemento = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, seletor)))
            print(f"     🔎 Campo encontrado: {seletor}")
            break
        except Exception:
            continue

    if elemento is None:
        raise Exception("❌ Campo de busca não encontrado com nenhum seletor.")

    # Força visibilidade e foco via JavaScript (resolve problema de versões novas)
    driver.execute_script("""
        arguments[0].removeAttribute('readonly');
        arguments[0].removeAttribute('disabled');
        arguments[0].style.display = 'block';
        arguments[0].style.visibility = 'visible';
        arguments[0].focus();
    """, elemento)
    time.sleep(0.5)

    return elemento

def safe_paste(element, text, driver):
    """
    Cola o texto no campo usando JavaScript + clipboard,
    garantindo que o evento de input seja disparado para o React/WhatsApp reconhecer.
    """
    pyperclip.copy(text)

    # Foca o elemento via JS antes de interagir
    driver.execute_script("arguments[0].focus();", element)
    time.sleep(0.3)

    # Limpa o campo de forma robusta
    element.send_keys(Keys.CONTROL + "a")
    time.sleep(0.2)
    element.send_keys(Keys.BACKSPACE)
    time.sleep(0.3)

    # Cola o conteúdo
    element.send_keys(Keys.CONTROL + "v")
    time.sleep(1.5)

# ==================== FLUXO PRINCIPAL ====================

def main():
    print("\n" + "="*60)
    print("🚀 AUTOMAÇÃO WHATSAPP - BASE: ali-meli.py")
    print("="*60)

    # 1. LEITURA DOS DADOS
    try:
        print(f"📂 Lendo Excel: {EXCEL_FILE}")
        dfs = pd.read_excel(EXCEL_FILE, sheet_name=SHEETS)
        # Concatena as abas e remove linhas vazias
        df = pd.concat(dfs.values(), ignore_index=True).dropna(subset=['Nome do Grupo', 'Mensagem'])
        print(f"✅ Excel lido: {len(df)} mensagens para enviar.")
    except Exception as e:
        print(f"❌ Erro ao ler Excel: {e}")
        return

    # 2. CONEXÃO COM CHROME (PORTA 9222)
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    try:
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20)
        print("🔗 Conectado ao Chrome com sucesso.")
    except Exception as e:
        print(f"❌ Falha na conexão: Verifique se o Chrome está aberto com --remote-debugging-port=9222. {e}")
        return

    # 2.1 LOCALIZAR ABA DO WHATSAPP
    whatsapp_handle = None
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if "web.whatsapp.com" in driver.current_url:
            whatsapp_handle = handle
            break

    if whatsapp_handle is None:
        print("❌ Aba do WhatsApp Web não encontrada.")
        return

    driver.switch_to.window(whatsapp_handle)
    driver.switch_to.default_content()
    print("✅ WhatsApp Web localizado.")
    time.sleep(2)

    # 3. PROCESSO DE ENVIO
    for idx, row in df.iterrows():
        grupo_nome = str(row['Nome do Grupo']).strip()
        mensagem = str(row['Mensagem']).strip()
        
        print(f"\n[{idx+1}/{len(df)}] 🔍 Processando: {grupo_nome}")

        try:
            # A. Localizar barra de pesquisa
            search_box = encontrar_campo_busca(wait, driver)
            
            # B. Digitar nome do grupo
            safe_paste(search_box, grupo_nome, driver)
            time.sleep(DELAY_SEARCH)

            # C. Seleção do Grupo
            try:
                # Estratégia: buscar o span que contém o nome exato do grupo no 'title'
                seletor_grupo = f'//span[@title="{grupo_nome}"]'
                span_nome = wait.until(EC.presence_of_element_located((By.XPATH, seletor_grupo)))
                
                # Navega até o container clicável da linha
                item_clicavel = span_nome.find_element(By.XPATH, './ancestor::div[@role="listitem" or @tabindex="-1"][1]')
                
                try:
                    item_clicavel.click()
                except:
                    driver.execute_script("arguments[0].click();", item_clicavel)
                print("     ✓ Grupo aberto via título exato.")
                
            except Exception:
                print("     ⚠️ Título exato não clicável, tentando ENTER...")
                search_box.send_keys(Keys.ENTER)

            time.sleep(DELAY_AFTER_OPEN_CHAT)

            # D. Envio da Mensagem
            msg_box = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')))
            
            safe_paste(msg_box, mensagem, driver)

            if "http" in mensagem.lower():
                print("     🔗 Aguardando prévia do link...")
                time.sleep(DELAY_AFTER_LINK)

            msg_box.send_keys(Keys.ENTER)
            print("     ✅ Mensagem enviada!")
            
            # Intervalo entre mensagens
            time.sleep(DELAY_BETWEEN_MESSAGES)

        except Exception as e:
            print(f"     ❌ Erro no grupo '{grupo_nome}': {str(e)[:100]}")
            # Limpa a busca para o próximo
            try:
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            except:
                pass
            time.sleep(2)

    print("\n" + "="*60)
    print("🏁 PROCESSO CONCLUÍDO!")
    print("="*60)

if __name__ == "__main__":
    main()
