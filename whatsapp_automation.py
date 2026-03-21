import pandas as pd
import time
import pyperclip
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==================== CONFIGURAÇÕES ====================
EXCEL_FILE = "aliexpress.xlsx"
SHEETS = ['Planilha14','Planilha15','Planilha16','Planilha17','Planilha18','Planilha19','Planilha20','Planilha21']

# Delays solicitados pelo usuário
DELAY_SEARCH = 5
DELAY_AFTER_OPEN_CHAT = 5
DELAY_AFTER_LINK = 10
DELAY_BETWEEN_MESSAGES = 8

# ==================== FUNÇÕES DE AUTOMAÇÃO ====================

def pesquisar_grupo(driver, wait, nome_grupo):
    """
    Pesquisa o grupo usando o seletor exato fornecido pelo usuário:
    <input role="textbox" aria-label="Pesquisar ou começar uma nova conversa" ...>
    """
    try:
        print(f"     🔍 Pesquisando: {nome_grupo}")
        
        # Seletor exato do input de busca fornecido no HTML
        seletor_busca = 'input[role="textbox"][aria-label="Pesquisar ou começar uma nova conversa"]'
        
        campo_busca = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, seletor_busca)))
        
        # Limpeza e digitação
        campo_busca.click()
        campo_busca.send_keys(Keys.CONTROL + "a")
        campo_busca.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        
        for char in nome_grupo:
            campo_busca.send_keys(char)
            time.sleep(0.05)
            
        time.sleep(DELAY_SEARCH)
        return True
    except Exception as e:
        print(f"     ❌ Erro ao localizar campo de busca: {e}")
        return False

def selecionar_grupo_da_lista(driver, nome_grupo):
    """
    Seleciona o grupo da lista de resultados usando a estrutura de row/gridcell fornecida:
    <div role="row" ...> <span title="NOME DO GRUPO" ...>
    """
    try:
        # Busca o elemento que contém o título do grupo nos resultados da pesquisa
        # O script tenta clicar no elemento que contém o texto exato ou parcial do grupo
        clicado = driver.execute_script("""
            const nomeAlvo = arguments[0].toLowerCase();
            // Busca em spans que costumam conter o título do grupo/contato
            const elementos = document.querySelectorAll('span[title], span[dir="auto"]');
            
            for (let el of elementos) {
                let texto = (el.getAttribute('title') || el.textContent || "").toLowerCase();
                if (texto.includes(nomeAlvo)) {
                    // Sobe até o container clicável (role="row" ou role="gridcell")
                    let container = el.closest('div[role="row"]') || el.closest('div[role="gridcell"]') || el;
                    container.click();
                    return true;
                }
            }
            return false;
        """, nome_grupo)
        
        if clicado:
            print(f"     ✅ Grupo '{nome_grupo}' selecionado.")
            return True
        else:
            print(f"     ⚠️ Grupo não encontrado na lista visual. Tentando ENTER...")
            # Fallback: pressionar ENTER no campo de busca
            driver.find_element(By.CSS_SELECTOR, 'input[role="textbox"][aria-label="Pesquisar ou começar uma nova conversa"]').send_keys(Keys.ENTER)
            return True
    except Exception as e:
        print(f"     ❌ Erro ao selecionar grupo: {e}")
        return False

def enviar_mensagem(driver, wait, mensagem):
    """
    Envia a mensagem na caixa de texto do chat aberto.
    """
    try:
        # Seletores comuns para a caixa de mensagem do WhatsApp Web
        seletores_msg = [
            'div[contenteditable="true"][role="textbox"]',
            'footer div[contenteditable="true"]',
            'div[data-tab="10"]'
        ]
        
        caixa_msg = None
        for sel in seletores_msg:
            try:
                caixa_msg = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                if caixa_msg: break
            except: continue
            
        if not caixa_msg:
            print("     ❌ Caixa de mensagem não encontrada.")
            return False
            
        caixa_msg.click()
        time.sleep(0.5)
        
        # Usa clipboard para garantir que emojis e links longos funcionem bem
        pyperclip.copy(mensagem)
        caixa_msg.send_keys(Keys.CONTROL + "v")
        
        # Delay solicitado para carregamento de links
        time.sleep(DELAY_AFTER_LINK)
        
        caixa_msg.send_keys(Keys.ENTER)
        print("     ✅ Mensagem enviada com sucesso.")
        return True
    except Exception as e:
        print(f"     ❌ Erro ao enviar mensagem: {e}")
        return False

# ==================== FLUXO PRINCIPAL ====================

def main():
    print("\n" + "="*60)
    print("🚀 AUTOMAÇÃO WHATSAPP - VERSÃO OTIMIZADA (HTML PRECISO)")
    print("="*60)

    # 1. Carregar Dados do Excel
    try:
        print(f"📂 Lendo Excel: {EXCEL_FILE}")
        all_data = []
        with pd.ExcelFile(EXCEL_FILE) as xls:
            for sheet in SHEETS:
                if sheet in xls.sheet_names:
                    df_sheet = pd.read_excel(xls, sheet_name=sheet)
                    # Identifica colunas dinamicamente
                    col_grupo = [c for c in df_sheet.columns if 'grupo' in c.lower()][0]
                    col_msg = [c for c in df_sheet.columns if 'mensagem' in c.lower()][0]
                    
                    temp_df = df_sheet[[col_grupo, col_msg]].dropna()
                    temp_df.columns = ['Grupo', 'Mensagem']
                    all_data.append(temp_df)
        
        df_final = pd.concat(all_data, ignore_index=True)
        print(f"✅ {len(df_final)} mensagens para processar.")
    except Exception as e:
        print(f"❌ Erro ao carregar Excel: {e}")
        return

    # 2. Conectar ao Navegador
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 15)
        print("✅ Conectado ao Chrome (Porta 9222)")
    except Exception as e:
        print("\n❌ ERRO: Não foi possível conectar ao Chrome.")
        print("👉 Comando necessário: chrome.exe --remote-debugging-port=9222")
        return

    # 3. Validar WhatsApp Web
    try:
        if "web.whatsapp.com" not in driver.current_url:
            for handle in driver.window_handles:
                driver.switch_to.window(handle)
                if "web.whatsapp.com" in driver.current_url: break
            else:
                print("❌ WhatsApp Web não encontrado.")
                return
    except:
        print("❌ Erro ao acessar o navegador.")
        return

    print("✅ WhatsApp Web detectado.")
    input("\n⚠️  Pressione ENTER para iniciar os envios...")

    # 4. Loop de Execução
    for idx, row in df_final.iterrows():
        grupo = str(row['Grupo']).strip()
        msg = str(row['Mensagem']).strip()
        
        print(f"\n[{idx+1}/{len(df_final)}] Processando: {grupo}")
        
        if pesquisar_grupo(driver, wait, grupo):
            if selecionar_grupo_da_lista(driver, grupo):
                time.sleep(DELAY_AFTER_OPEN_CHAT)
                enviar_mensagem(driver, wait, msg)
        
        print(f"     ⏳ Intervalo de {DELAY_BETWEEN_MESSAGES}s...")
        time.sleep(DELAY_BETWEEN_MESSAGES)

    print("\n" + "="*60)
    print("🏁 PROCESSO CONCLUÍDO COM SUCESSO!")
    print("="*60)

if __name__ == "__main__":
    main()
