import pandas as pd
import time
import pyperclip
import re
import sys
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

# ==================== FUNÇÕES AUXILIARES ====================

def debug_nomes_grupos(driver):
    """Função para debug - mostra todos os grupos encontrados na barra lateral"""
    print("\n     🔍 LISTANDO GRUPOS DISPONÍVEIS NA BARRA LATERAL:")
    try:
        grupos = driver.execute_script("""
            let grupos = [];
            let elementos = document.querySelectorAll('span[title], div[role="listitem"] span');
            elementos.forEach(el => {
                let texto = el.getAttribute('title') || el.textContent;
                if (texto && texto.trim().length > 0 && texto.length < 50) {
                    grupos.push(texto.trim());
                }
            });
            return [...new Set(grupos)].slice(0, 15); 
        """)
        for i, grupo in enumerate(grupos, 1):
            print(f"     {i}. {grupo}")
    except:
        print("     ⚠️ Não foi possível listar os grupos.")
    print()

def encontrar_campo_busca(wait):
    """Encontra o campo de busca do WhatsApp com seletores atualizados"""
    seletores = [
        (By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'),
        (By.XPATH, '//div[@contenteditable="true"][@aria-label="Pesquisar ou começar uma nova conversa"]'),
        (By.CSS_SELECTOR, 'div[contenteditable="true"][data-tab="3"]'),
        (By.CSS_SELECTOR, 'div[role="textbox"][aria-label*="Pesquisar"]')
    ]
    
    for by, seletor in seletores:
        try:
            el = wait.until(EC.element_to_be_clickable((by, seletor)))
            return el
        except:
            continue
    return None

def buscar_e_clicar_grupo(driver, wait, grupo_nome):
    """Busca e clica no grupo com lógica de limpeza e clique forçado"""
    try:
        print(f"     🔍 Buscando: {grupo_nome}")
        campo_busca = encontrar_campo_busca(wait)
        
        if not campo_busca:
            print("     ❌ Campo de busca não encontrado.")
            return False

        # Limpeza robusta do campo
        campo_busca.click()
        time.sleep(0.5)
        campo_busca.send_keys(Keys.CONTROL + "a")
        campo_busca.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        
        # Digitação pausada
        for char in grupo_nome:
            campo_busca.send_keys(char)
            time.sleep(0.05)
        
        time.sleep(DELAY_SEARCH)

        # Tenta clicar no resultado via JavaScript (mais confiável para elementos dinâmicos)
        clicado = driver.execute_script("""
            const nome = arguments[0].toLowerCase();
            const spans = document.querySelectorAll('span[title]');
            for (let span of spans) {
                if (span.title.toLowerCase().includes(nome) || span.textContent.toLowerCase().includes(nome)) {
                    let target = span.closest('div[role="row"]') || span.closest('div[data-testid="cell-frame-container"]') || span;
                    target.click();
                    return true;
                }
            }
            return false;
        """, grupo_nome)

        if clicado:
            print(f"     ✅ Grupo clicado com sucesso.")
            return True
        else:
            print(f"     🔄 Tentando abrir via ENTER...")
            campo_busca.send_keys(Keys.ENTER)
            return True
            
    except Exception as e:
        print(f"     ⚠️ Erro na busca: {str(e)[:50]}")
    return False

def enviar_mensagem_simples(driver, wait, mensagem):
    """Envia mensagem usando clipboard para evitar problemas com caracteres especiais"""
    try:
        seletores = [
            (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'),
            (By.CSS_SELECTOR, 'footer div[contenteditable="true"]'),
            (By.CSS_SELECTOR, 'div[role="textbox"][aria-label*="Digite uma mensagem"]')
        ]
        
        caixa_msg = None
        for by, seletor in seletores:
            try:
                caixa_msg = wait.until(EC.element_to_be_clickable((by, seletor)))
                break
            except:
                continue
        
        if not caixa_msg:
            print("     ❌ Caixa de mensagem não encontrada.")
            return False
        
        caixa_msg.click()
        time.sleep(0.5)
        
        # Copia para o clipboard e cola
        pyperclip.copy(mensagem)
        caixa_msg.send_keys(Keys.CONTROL + "v")
        
        time.sleep(DELAY_AFTER_LINK)
        caixa_msg.send_keys(Keys.ENTER)
        
        print("     ✅ Mensagem enviada.")
        return True
    except Exception as e:
        print(f"     ❌ Erro no envio: {str(e)[:50]}")
        return False

def verificar_grupo_aberto(driver, grupo_nome):
    """Verifica se o chat aberto é o correto"""
    try:
        # Tenta múltiplos seletores para o título do chat
        seletores_titulo = [
            'span[data-testid="conversation-info-header-chat-title"]',
            'div[data-testid="conversation-title"]',
            'header span[title]'
        ]
        
        titulo_atual = ""
        for seletor in seletores_titulo:
            try:
                el = driver.find_element(By.CSS_SELECTOR, seletor)
                titulo_atual = el.get_attribute('title') or el.text
                if titulo_atual: break
            except:
                continue
        
        if not titulo_atual:
            return True # Fallback se não conseguir ler o título
            
        print(f"     📌 Chat aberto: {titulo_atual}")
        nome_limpo = re.sub(r'[^\w]', '', grupo_nome.lower())
        titulo_limpo = re.sub(r'[^\w]', '', titulo_atual.lower())
        
        return nome_limpo in titulo_limpo or titulo_limpo in nome_limpo
    except:
        return True

# ==================== EXECUÇÃO ====================

def main():
    print("\n" + "="*60)
    print("🚀 INICIANDO AUTOMAÇÃO WHATSAPP")
    print("="*60)

    # 1. Carregar Excel
    try:
        print(f"📂 Lendo: {EXCEL_FILE}")
        all_data = []
        with pd.ExcelFile(EXCEL_FILE) as xls:
            for sheet in SHEETS:
                if sheet in xls.sheet_names:
                    df_sheet = pd.read_excel(xls, sheet_name=sheet)
                    # Tenta encontrar as colunas corretas independente do nome exato
                    col_grupo = [c for c in df_sheet.columns if 'grupo' in c.lower()][0]
                    col_msg = [c for c in df_sheet.columns if 'mensagem' in c.lower()][0]
                    
                    temp_df = df_sheet[[col_grupo, col_msg]].dropna()
                    temp_df.columns = ['Grupo', 'Mensagem']
                    all_data.append(temp_df)
        
        if not all_data:
            print("❌ Nenhuma aba encontrada ou abas vazias.")
            return
            
        df_final = pd.concat(all_data, ignore_index=True)
        print(f"✅ {len(df_final)} mensagens carregadas.")
    except Exception as e:
        print(f"❌ Erro ao processar Excel: {e}")
        return

    # 2. Conectar ao Chrome
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 15)
        print("✅ Conectado ao Chrome (Porta 9222)")
    except Exception as e:
        print("\n❌ ERRO: Não foi possível conectar ao Chrome.")
        print("👉 Certifique-se de que o Chrome foi aberto com: chrome.exe --remote-debugging-port=9222")
        return

    # 3. Validar WhatsApp
    try:
        if "web.whatsapp.com" not in driver.current_url:
            print("⚠️  WhatsApp Web não está na aba ativa. Tentando localizar...")
            for handle in driver.window_handles:
                driver.switch_to.window(handle)
                if "web.whatsapp.com" in driver.current_url:
                    break
            else:
                print("❌ WhatsApp Web não encontrado. Abra-o no navegador.")
                return
    except:
        print("❌ Erro ao acessar abas do navegador.")
        return

    print("✅ WhatsApp Web detectado.")
    debug_nomes_grupos(driver)
    input("\n⚠️  Pressione ENTER para começar os envios...")

    # 4. Loop de Envio
    for idx, row in df_final.iterrows():
        grupo = str(row['Grupo']).strip()
        msg = str(row['Mensagem']).strip()
        
        print(f"\n[{idx+1}/{len(df_final)}] Grupo: {grupo}")
        
        if buscar_e_clicar_grupo(driver, wait, grupo):
            time.sleep(DELAY_AFTER_OPEN_CHAT)
            
            if verificar_grupo_aberto(driver, grupo):
                enviar_mensagem_simples(driver, wait, msg)
            else:
                print("     ❌ Falha na validação do nome do grupo.")
        
        print(f"     ⏳ Aguardando {DELAY_BETWEEN_MESSAGES}s...")
        time.sleep(DELAY_BETWEEN_MESSAGES)

    print("\n" + "="*60)
    print("🏁 PROCESSO CONCLUÍDO")
    print("="*60)

if __name__ == "__main__":
    main()
