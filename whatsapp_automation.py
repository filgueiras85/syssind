import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ==================== CONFIGURAÇÕES ====================
EXCEL_FILE = "aliexpress.xlsx"
SHEETS = ['Planilha14', 'Planilha15', 'Planilha16', 'Planilha17', 'Planilha18', 'Planilha19', 'Planilha20', 'Planilha21']
DELAY_SEARCH = 2
DELAY_AFTER_OPEN_CHAT = 4
DELAY_AFTER_LINK = 10
DELAY_BETWEEN_MESSAGES = 5

def whatsapp_bot():
    """
    Script para automatizar o envio de mensagens para grupos no WhatsApp Web
    lendo dados de um arquivo Excel e respeitando os atrasos configurados.
    """
    
    # Configuração do Chrome Driver
    options = webdriver.ChromeOptions()
    # options.add_argument("user-data-dir=/home/ubuntu/.config/google-chrome/whatsapp_session")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        print("Abrindo WhatsApp Web...")
        driver.get("https://web.whatsapp.com")
        
        print("Por favor, escaneie o QR Code se necessário.")
        # Espera até que a lista de conversas esteja carregada
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//div[@role="gridcell"]'))
        )
        
        # Iterar pelas abas do Excel
        for sheet in SHEETS:
            try:
                print(f"\n--- Processando aba: {sheet} ---")
                # Lendo a aba específica do Excel
                # Assume-se que a primeira coluna é o nome do grupo e a segunda é a mensagem
                df = pd.read_excel(EXCEL_FILE, sheet_name=sheet)
                
                for index, row in df.iterrows():
                    group_name = str(row.iloc[0])  # Primeira coluna: Nome do Grupo
                    message = str(row.iloc[1])     # Segunda coluna: Mensagem
                    
                    print(f"Pesquisando pelo grupo: {group_name}")
                    
                    # Localizar a caixa de pesquisa
                    search_box_xpath = '//div[@contenteditable="true"][@data-tab="3"]'
                    search_box = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, search_box_xpath))
                    )
                    
                    # Limpar e digitar o nome do grupo
                    search_box.click()
                    search_box.send_keys(Keys.CONTROL + "a")
                    search_box.send_keys(Keys.BACKSPACE)
                    search_box.send_keys(group_name)
                    
                    time.sleep(DELAY_SEARCH)
                    search_box.send_keys(Keys.ENTER)
                    
                    # Aguardar o chat abrir
                    time.sleep(DELAY_AFTER_OPEN_CHAT)
                    
                    print(f"Enviando mensagem para '{group_name}'...")
                    
                    # Localizar a caixa de mensagem
                    message_box_xpath = '//div[@contenteditable="true"][@data-tab="10"]'
                    message_box = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, message_box_xpath))
                    )
                    
                    # Digitar a mensagem e enviar
                    message_box.send_keys(message)
                    time.sleep(1)
                    message_box.send_keys(Keys.ENTER)
                    
                    print(f"Mensagem enviada com sucesso!")
                    
                    # Delay após o envio (pode ser usado para links carregarem ou apenas pausa)
                    time.sleep(DELAY_AFTER_LINK)
                    
                    # Delay entre mensagens de diferentes grupos
                    time.sleep(DELAY_BETWEEN_MESSAGES)
                    
            except Exception as e:
                print(f"Erro ao processar a aba '{sheet}': {str(e)}")
                continue
                
        print("\nProcesso concluído com sucesso!")
        
    except Exception as e:
        print(f"Ocorreu um erro geral: {str(e)}")
    finally:
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    whatsapp_bot()
