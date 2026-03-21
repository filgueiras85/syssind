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

# ==================== FUNÇÕES AUXILIARES ====================

def debug_nomes_grupos(driver):
    """Função para debug - mostra todos os grupos encontrados"""
    print("\n     🔍 LISTANDO GRUPOS DISPONÍVEIS:")
    grupos = driver.execute_script("""
        let grupos = [];
        let elementos = document.querySelectorAll('div[role="row"], div[data-testid="cell-frame-container"]');
        elementos.forEach(el => {
            let texto = el.textContent || el.innerText;
            if (texto && texto.trim().length > 0 && texto.length < 100) {
                grupos.push(texto.trim());
            }
        });
        return grupos.slice(0, 20);  // Mostra apenas os primeiros 20
    """)
    
    for i, grupo in enumerate(grupos, 1):
        print(f"     {i}. {grupo}")
    print()
    return grupos

def encontrar_campo_busca(wait, driver):
    """Encontra o campo de busca do WhatsApp"""
    seletores = [
        'div[contenteditable="true"][data-tab="3"]',
        'div[contenteditable="true"][aria-label*="Pesquisar"]',
        'div[contenteditable="true"][title*="Pesquisar"]',
    ]
    
    for seletor in seletores:
        try:
            el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, seletor)))
            print(f"     🔎 Campo de busca encontrado")
            return el
        except:
            continue
    
    raise Exception("❌ Campo de busca não encontrado")

def buscar_e_clicar_grupo(driver, wait, grupo_nome):
    """Busca e clica no grupo usando múltiplas estratégias"""
    
    try:
        print(f"     🔍 Buscando: {grupo_nome}")
        
        # Limpa o campo de busca
        campo_busca = encontrar_campo_busca(wait, driver)
        campo_busca.click()
        # Usar CONTROL+A e BACKSPACE para garantir limpeza
        campo_busca.send_keys(Keys.CONTROL + "a")
        campo_busca.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        
        # Digita o nome do grupo
        for char in grupo_nome:
            campo_busca.send_keys(char)
            time.sleep(0.05)
        
        # Delay após pesquisa solicitado
        time.sleep(DELAY_SEARCH)
        
        # Tenta encontrar o grupo na lista via script para maior precisão
        grupo_encontrado = driver.execute_script(f"""
            const nomeBusca = arguments[0];
            const elementos = document.querySelectorAll('div[role="row"], div[data-testid="cell-frame-container"]');
            
            for (let el of elementos) {{
                let texto = el.textContent || el.innerText;
                if (texto && texto.includes(nomeBusca)) {{
                    el.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                    return el;
                }}
            }}
            return null;
        """, grupo_nome)
        
        if grupo_encontrado:
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", grupo_encontrado)
            print(f"     ✅ Grupo encontrado e clicado")
            return True
        else:
            # Tenta a estratégia do ENTER se não encontrar o elemento clicável
            campo_busca.send_keys(Keys.ENTER)
            print(f"     🔄 Tentando abrir via ENTER...")
            return True
            
    except Exception as e:
        print(f"     ⚠️ Erro ao buscar grupo: {e}")
    
    return False

def enviar_mensagem_simples(driver, wait, mensagem):
    """Envia mensagem de forma simples e confiável"""
    try:
        # Tenta encontrar a caixa de mensagem
        seletores = [
            'div[contenteditable="true"][role="textbox"]',
            'div[contenteditable="true"][data-lexical-editor="true"]',
            'footer div[contenteditable="true"]',
            '#main div[contenteditable="true"]'
        ]
        
        caixa_msg = None
        for seletor in seletores:
            try:
                caixa_msg = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, seletor)))
                print(f"     📝 Caixa de mensagem encontrada")
                break
            except:
                continue
        
        if not caixa_msg:
            print("     ❌ Caixa de mensagem não encontrada")
            return False
        
        # Limpa e foca na caixa
        caixa_msg.click()
        # Garante que está limpo
        caixa_msg.send_keys(Keys.CONTROL + "a")
        caixa_msg.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        
        # Digita a mensagem usando clipboard para manter formatação/emojis
        pyperclip.copy(mensagem)
        caixa_msg.send_keys(Keys.CONTROL + "v")
        
        # Delay após colar o link/mensagem solicitado
        time.sleep(DELAY_AFTER_LINK)
        
        # Envia
        caixa_msg.send_keys(Keys.ENTER)
        print("     ✅ Mensagem enviada")
        return True
        
    except Exception as e:
        print(f"     ❌ Erro ao enviar mensagem: {e}")
        return False

def verificar_grupo_aberto(driver, grupo_nome):
    """Verifica se o grupo correto foi aberto"""
    try:
        header = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="conversation-title"]')
        texto_header = header.text
        print(f"     📌 Header da conversa: {texto_header}")
        
        # Verifica se o nome do grupo está no header (ignora case e espaços extras)
        if grupo_nome.lower().strip() in texto_header.lower().strip() or texto_header.lower().strip() in grupo_nome.lower().strip():
            return True
            
    except:
        pass
    
    return False

# ==================== INÍCIO DO SCRIPT ====================

def main():
    print("=" * 60)
    print("ENVIO DE MENSAGENS PARA WHATSAPP WEB (BASEADO NO SCRIPT NOVO)")
    print("=" * 60)

    # 1. Leitura do Excel (Múltiplas abas)
    try:
        print(f"📂 Lendo arquivo: {EXCEL_FILE}")
        dfs = pd.read_excel(EXCEL_FILE, sheet_name=SHEETS)
        # Concatena todas as abas e remove linhas onde o nome do grupo ou mensagem estão vazios
        df = pd.concat(dfs, ignore_index=True).dropna(subset=['Nome do Grupo', 'Mensagem'])
        df = df.astype({'Nome do Grupo': str, 'Mensagem': str})
        print(f"✅ {len(df)} mensagens carregadas de {len(SHEETS)} abas.")
    except Exception as e:
        print(f"❌ Erro ao ler Excel: {e}")
        return

    # 2. Conectar ao Chrome (Usando porta de debug como no seu script base)
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    try:
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20)
        print("✅ Conectado ao Chrome (Porta 9222)")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        print("\n👉 Lembre-se de abrir o Chrome com o comando:")
        print("chrome.exe --remote-debugging-port=9222")
        return

    # 3. Verificar WhatsApp Web
    whatsapp_handle = None
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if "web.whatsapp.com" in driver.current_url:
            whatsapp_handle = handle
            break

    if not whatsapp_handle:
        print("❌ WhatsApp Web não encontrado nas abas abertas.")
        return

    driver.switch_to.window(whatsapp_handle)
    print("✅ WhatsApp Web localizado.")
    time.sleep(3)

    # 4. Modo debug inicial
    debug_nomes_grupos(driver)
    input("\n⚠️  Verifique se os grupos estão visíveis. Pressione ENTER para iniciar os envios...")

    # 5. Loop de Envio
    sucesso = 0
    falhas = 0

    for idx, row in df.iterrows():
        grupo = row['Nome do Grupo'].strip()
        msg = row['Mensagem'].strip()
        
        print(f"\n{'='*50}")
        print(f"[{idx+1}/{len(df)}] Processando: {grupo}")
        print(f"     Mensagem: {msg[:40]}...")
        print('='*50)
        
        try:
            # Busca e clica no grupo
            if buscar_e_clicar_grupo(driver, wait, grupo):
                # Delay após abrir o chat solicitado
                time.sleep(DELAY_AFTER_OPEN_CHAT)
                
                # Verifica se o grupo correto foi aberto
                if verificar_grupo_aberto(driver, grupo):
                    print("     ✅ Grupo validado")
                    
                    # Envia mensagem
                    if enviar_mensagem_simples(driver, wait, msg):
                        sucesso += 1
                    else:
                        falhas += 1
                else:
                    falhas += 1
                    print(f"     ❌ Grupo aberto não corresponde ao esperado")
            else:
                falhas += 1
                print(f"     ❌ Falha ao localizar o grupo")
                
        except Exception as e:
            falhas += 1
            print(f"     ❌ Erro inesperado: {e}")
        
        # Delay entre mensagens solicitado
        print(f"     ⏳ Aguardando {DELAY_BETWEEN_MESSAGES}s para o próximo...")
        time.sleep(DELAY_BETWEEN_MESSAGES)

    # 6. Resumo Final
    print("\n" + "="*60)
    print("RESUMO DA OPERAÇÃO")
    print("="*60)
    print(f"✅ Sucesso: {sucesso}")
    print(f"❌ Falhas:  {falhas}")
    print(f"📊 Total:   {sucesso + falhas}")
    print("="*60)

    fechar = input("\nDeseja encerrar o navegador? (s/n): ")
    if fechar.lower() == 's':
        driver.quit()
        print("Navegador encerrado.")

if __name__ == "__main__":
    main()
