import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException


options = webdriver.ChromeOptions()
options.add_argument("headless")
driver = webdriver.Chrome(options=options)
bot = commands.Bot(command_prefix='!',intents=discord.Intents.all())
listUrl = 'https://teamfighttactics.leagueoflegends.com/ko-kr/news/'
response = requests.get(listUrl)
c = 'sc-ce9b75fd-0'

driver.get(listUrl)

async def on_ready(self):
    await self.change_presence(status=discord.Status.online)

@bot.command(name="patch")
async def patch(ctx):

    print("start")

    try:
        close = driver.find_element(By.CLASS_NAME, 'osano-cm-dialog__close')
        close.click()  # 요소가 존재하면 클릭
    except NoSuchElementException:
        print("Close button not found")

    action = ActionChains(driver)

    while (True) :
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')


        title = soup.find('div', string=lambda text: text and "패치 노트" in text)

        if title:
            tagText = title.text.strip()
            xpath = f"//*[contains(text(), '{tagText}')]"

            print(xpath)
            try:
                titleCard = driver.find_element(By.XPATH, xpath)
                action.move_to_element(titleCard).perform()
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                titleCard.click()
                break
            except Exception as e:
                print(f"오류 발생: {e}")
                break
        else:
            try:
                footer = driver.find_element(By.CLASS_NAME, 'riotbar-footer-logo')
                action.move_to_element(footer).perform()

                ctaButton = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "cta"))
                )
                ctaButton.click()
            except Exception as e:
                print(f"cta 버튼 클릭 실패: {e}")
                break

        driver.implicitly_wait(10)

    await getPatchNote(ctx)
    

async def getPatchNote(ctx):
    # 패치 노트 읽어오기
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "richText"))
    )
    
    print(driver.current_url)
    patchPage = requests.get(driver.current_url)

    patchSoup = BeautifulSoup(patchPage.content, 'html.parser')

    discord_message = []
    image_urls = []

    isLi = False

    charCnt = 0

    
    if (patchPage.status_code == 200):
        content_divs = patchSoup.find_all('div', id='patch-notes-container')
        
        for div in content_divs:
            for element in div.find_all(['h2', 'h4', 'li', 'img', 'blockquote']):
                if element.name == 'h2':
                    if element.get('id') == 'patch-top':
                        continue
                    if isLi:
                        isLi = False
                    if discord_message:
                        combined_message = "\n".join(discord_message)
                        await ctx.send(combined_message)
                        discord_message = []
                    discord_message.append(f"\n# {element.get_text(strip=True)}\n")
                elif element.name == 'h4':
                    if isLi:
                        isLi = False
                    if discord_message:
                        combined_message = "\n".join(discord_message)
                        await ctx.send(combined_message)
                        discord_message = []
                    discord_message.append(f"\n## {element.get_text(strip=True)}\n")
                elif element.name == 'li':
                    li_text = ""
                    
                    for child in element.contents:
                        if child.name == 'strong':
                            strong_text = f" **{child.get_text(strip=True)}** "
                            li_text += strong_text
                        else:
                            li_text += child.get_text(strip=True)

                    messageResult = f"* {li_text}\n"

                    if isLi == False:
                        messageResult = ">>> " + messageResult
                        isLi = True
                        charCnt = 0

                    if charCnt + len(messageResult) >= 1990:
                        combined_message = "\n".join(discord_message)
                        await ctx.send(combined_message)
                        charCnt = 0
                        messageResult = ">>> \n" + messageResult
                        discord_message = []

                    discord_message.append(messageResult)
                    charCnt += len(messageResult)
                elif element.name == 'blockquote':
                    quote = "### :speech_balloon: "

                    for child in element.contents:
                        if child.name == 'br':
                            quote += "\n ### "
                        else:
                            quote += f" {child.get_text(strip=True)}"

                    discord_message.append(quote)

                    combined_message = "\n".join(discord_message)
                    await ctx.send(combined_message)
                    discord_message = []
                elif element.name == 'div' and element['class'][0] == 'content-border':
                    for child in element.contents:
                        if child.name == 'img':
                            url = child.get_text(strip=True)
                            img = requests.get(url).content
                            await ctx.send(file=discord.File(fp=img))

                        


            # Discord 메시지 제한 (2000자) 대비 슬라이싱
            combined_message = "\n".join(discord_message)
            if len(combined_message) > 2000:
                for i in range(0, len(combined_message), 2000):
                    await ctx.send(combined_message[i:i+2000])
            else:
                await ctx.send(combined_message)

            await ctx.send(f"-# url: " + driver.current_url)


async def sendMessage(ctx, discord_message):
    combined_message = "\n".join(discord_message)
    await ctx.send(combined_message)


bot.run(TOKEN)