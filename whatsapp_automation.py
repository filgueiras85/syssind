import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def whatsapp_bot(group_names, message):
    """
    Script para automatizar o envio de mensagens para grupos no WhatsApp Web.
    
    :param group_names: Lista de nomes de grupos para pesquisar.
    :param message: Mensagem a ser enviada.
    """
    
    # Configuração do Chrome Driver
    options = webdriver.ChromeOptions()
    # Usar um perfil de usuário para manter a sessão logada (opcional, mas recomendado)
    # options.add_argument("user-data-dir=/home/ubuntu/.config/google-chrome/whatsapp_session")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        print("Abrindo WhatsApp Web...")
        driver.get("https://web.whatsapp.com")
        
        print("Por favor, escaneie o QR Code se necessário.")
        # Espera até que a lista de conversas esteja carregada (indicando login bem-sucedido)
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//div[@role="gridcell"]'))
        )
        
        for group_name in group_names:
            try:
                print(f"Pesquisando pelo grupo: {group_name}")
                
                # Localizar a caixa de pesquisa baseada no HTML fornecido
                # O placeholder é "Pesquisar ou começar uma nova conversa"
                search_box_xpath = '//div[@contenteditable="true"][@data-tab="3"]'
                # Alternativa baseada no input role="textbox"
                search_box_alt_xpath = '//input[@role="textbox"][@aria-label="Pesquisar ou começar uma nova conversa"]'
                
                try:
                    search_box = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, search_box_xpath))
                    )
                except:
                    search_box = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, search_box_alt_xpath))
                    )
                
                # Limpar e digitar o nome do grupo
                search_box.click()
                search_box.send_keys(Keys.CONTROL + "a")
                search_box.send_keys(Keys.BACKSPACE)
                search_box.send_keys(group_name)
                time.sleep(2)
                search_box.send_keys(Keys.ENTER)
                
                print(f"Grupo '{group_name}' selecionado. Enviando mensagem...")
                
                # Localizar a caixa de mensagem
                # Geralmente é um div com contenteditable="true" e data-tab="10" ou similar
                message_box_xpath = '//div[@contenteditable="true"][@data-tab="10"]'
                
                message_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, message_box_xpath))
                )
                
                # Digitar a mensagem e enviar
                message_box.send_keys(message)
                time.sleep(1)
                message_box.send_keys(Keys.ENTER)
                
                print(f"Mensagem enviada para '{group_name}' com sucesso!")
                time.sleep(2) # Pequena pausa entre envios
                
            except Exception as e:
                print(f"Erro ao processar o grupo '{group_name}': {str(e)}")
                continue
                
        print("Processo concluído.")
        
    except Exception as e:
        print(f"Ocorreu um erro geral: {str(e)}")
    finally:
        # Manter o navegador aberto por alguns segundos antes de fechar
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    # Exemplo de uso
    grupos = ["NOTÍCIAS RONDÔNIA", "Grupo de Teste"]
    mensagem_texto = "Olá! Esta é uma mensagem automática enviada via script Python."
    
    whatsapp_bot(grupos, mensagem_texto)
