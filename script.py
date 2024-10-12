import threading
import traceback
import random
from colorama import Fore, Style, init
from screeninfo import get_monitors
from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, WebDriverException, ElementClickInterceptedException
import time
import pyautogui

random_sleep_time = random.randint(60, 120)

def load_data(file_path):
    with open(file_path, 'r') as file:
        useragents = file.readlines()
    return [agent.strip() for agent in useragents]
def close_popup(driver):
    try:
        close_buttons = driver.find_elements(By.CLASS_NAME, 'slidedown-body-message')
        if close_buttons:
            close_buttons[0].click()
            print("Đã đóng popup.")
    except Exception as e:
        print(f"Lỗi khi đóng popup: {e}")

def load_browser(url, position, user_agent, proxy, max_retries=3):
    driver = None
    retry_count = 0  

    options = ChromeOptions()
    service_path = 'chromedriver.exe'
    options.add_argument("--log-level=3")   
    options.add_argument("--silent")  
    options.add_argument(f"--proxy-server={proxy}")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f"user-agent={user_agent}")
    service = ChromeService(executable_path=service_path)
    driver = Chrome(options=options, service=service)

    try:
        screen_width = get_monitors()[0].width
        browsers_per_row = 3
        browser_width = screen_width // browsers_per_row
        browser_height = 400

        driver.set_window_size(browser_width, browser_height)

        x_position = (position % browsers_per_row) * browser_width
        y_position = (position // browsers_per_row) * (browser_height + 10)
        driver.set_window_position(x_position, y_position)

        while retry_count < max_retries:
            # time.sleep(10)
            try:
                print(f"Bắt đầu tải trang: {url} (Tải lần thứ {retry_count + 1})")
                
                driver.get(url)
                
                scroll_time = 180
                scroll_pause_time = random.uniform(0.5, 0.8)
                scroll_height = 0
                
                start_time = time.time()
                while (time.time() - start_time) < scroll_time:
                    new_scroll_height = driver.execute_script("return document.body.scrollHeight")
                    if scroll_height >= new_scroll_height:
                        break
                    scroll_height += 100
                    driver.execute_script(f"window.scrollTo(0, {scroll_height});")
                    time.sleep(scroll_pause_time)

                half_page_height = driver.execute_script("return document.body.scrollHeight") / 2
                while scroll_height > half_page_height:
                    scroll_height -= 100
                    driver.execute_script(f"window.scrollTo(0, {scroll_height});")
                    time.sleep(scroll_pause_time)

                # time.sleep(2)

                current_url = driver.current_url
                links = driver.find_elements(By.TAG_NAME, 'a')

                if links:
                    try:
                        valid_links = [link.get_attribute("href") for link in links 
                                       if link.get_attribute("href") and '#' not in link.get_attribute("href") 
                                       and link.get_attribute("href") != current_url]

                        if valid_links:
                            random_link = random.choice(valid_links)
                            print(f"Chọn liên kết ngẫu nhiên: {random_link}")

                            try:
                                driver.get(random_link)
                                print(f"Đã truy cập vào liên kết: {random_link}")

                                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                                print("Trang đã tải xong.")
                                time.sleep(2)
                                driver.execute_script("window.scrollBy(0, 300);")   

                                time.sleep(random.randint(30, 80)) 
                                break
                            except Exception as e:
                                print(f"Lỗi khi truy cập liên kết: ")
                                continue
                        else:
                            print("Không tìm thấy liên kết nào hợp lệ.")
                    except Exception as e:
                        print(f"Lỗi khi xử lý các liên kết: ")
                else:
                    print("Không tìm thấy liên kết nào.")

                time.sleep(25)
                break  

            except Exception as e:
                retry_count += 1   
                print(f"Lỗi trong luồng trình duyệt: {e}")
                traceback.print_exc()
                if retry_count < max_retries:
                    print(f"Tải lại lần thứ {retry_count + 1}")
                else:
                    print("Đã Tải tối đa số lần quy định, dừng lại.")

    finally:
        if driver:
            driver.quit()
        print(f"Đã đóng trình duyệt cho URL: {url}")


def run_multiple_browsers(urls, user_agent_get, proxy_get, batch_size):
    useragents = load_data('useragents.txt')
    proxies = load_data('proxies.txt')

    if not useragents and not user_agent_get:
        print(f"{Fore.RED}Không có user agent nào và cũng không được cung cấp!{Fore.RESET}")
        return
    if not proxies and not proxy_get:
        print(f"{Fore.RED}Không có proxy nào và cũng không được cung cấp!{Fore.RESET}")
        return

    for batch_start in range(0, len(urls), batch_size):
        threads = []
        batch_urls = urls[batch_start:batch_start + batch_size]  # Lấy một LUỒNG các URL
        
        print(f"\n\n{Fore.MAGENTA}{Style.BRIGHT}------------------- LUỒNG {batch_start // batch_size + 1} ----------------")

        for index, url in enumerate(batch_urls):
            user_agent = user_agent_get if user_agent_get else random.choice(useragents)
            proxy = proxy_get if proxy_get else random.choice(proxies)

            print(f"{Fore.YELLOW}Website: {Fore.BLUE}{url}")
            print(f"{Fore.GREEN}User agent đang sử dụng: {Fore.CYAN}{user_agent}")
            print(f"{Fore.GREEN}Proxy đang sử dụng: {Fore.CYAN}{proxy}")

            thread = threading.Thread(target=load_browser, args=(url, index, user_agent, proxy))
            threads.append(thread)
            thread.start()

            time.sleep(1)

        for thread in threads:
            thread.join()

        print(f"{Fore.MAGENTA}{Style.BRIGHT}------------------- KẾT THÚC LUỒNG {batch_start // batch_size + 1} ----------------\n\n")

        time.sleep(5)   
        thread.join()

if __name__ == "__main__":
    all_urls = load_data('urls.txt')

    while True:
        try:
            num_urls = int(input(f"{Style.BRIGHT}{Fore.BLUE}Có {len(all_urls)} URL có sẵn. Nhập số lượng URL muốn chạy (tối đa {len(all_urls)}): {Fore.RESET}"))
            if 1 <= num_urls <= len(all_urls):
                break
            else:
                print(f"{Fore.RED}Vui lòng nhập một số từ 1 đến {len(all_urls)}.{Fore.RESET}")
        except ValueError:
            print(f"{Fore.YELLOW}Vui lòng nhập một số nguyên hợp lệ.{Fore.RESET}")

    while True:
        try:
            batch_size = int(input(f"{Style.BRIGHT}{Fore.BLUE}Nhập số lượng tab muốn mở đồng thời (tối đa {num_urls}): {Fore.RESET}"))
            if 1 <= batch_size <= num_urls:
                break
            else:
                print(f"{Fore.RED}Vui lòng nhập một số từ 1 đến {num_urls}.{Fore.RESET}")
        except ValueError:
            print(f"{Fore.YELLOW}Vui lòng nhập một số nguyên hợp lệ.{Fore.RESET}")

    user_agent = input("Nhập user agent muốn sử dụng (hoặc để trống để sử dụng ngẫu nhiên): ")
    proxy = input("Nhập proxy muốn sử dụng (hoặc để trống để sử dụng ngẫu nhiên): ")

    selected_urls = all_urls[:num_urls]

    run_multiple_browsers(selected_urls, user_agent, proxy, batch_size)

    print(f"\n\n{Fore.MAGENTA}{Style.BRIGHT}-------------------END----------------\n\n")
