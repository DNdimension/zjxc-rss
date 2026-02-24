import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import pytz
import os

# ===== 配置区 =====
TARGET_URL = "https://zjnews.zjol.com.cn/zjxc/"
OUTPUT_FILE = "docs/rss.xml"
MAX_ARTICLES = 30  # 抓取最新30篇

# RSS频道信息
BLOG_NAME = "浙江宣传"
BLOG_LINK = TARGET_URL
BLOG_DESCRIPTION = "自动生成的浙江宣传 RSS 订阅源（基于真实网页结构）"

def fetch_articles():
    """抓取网页，提取文章列表（精确匹配实际HTML结构）"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"正在抓取: {TARGET_URL}")
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"抓取失败: {e}")
        return []

    articles = []
    
    # 精确找到文章列表容器
    ul_container = soup.find('ul', class_='listUl')
    if not ul_container:
        print("错误：未找到 class='listUl' 的列表容器")
        return []
    
    # 遍历每个 li.listLi
    for li in ul_container.find_all('li', class_='listLi'):
        # 1. 提取时间
        span_time = li.find('span', class_='listSpan')
        if not span_time:
            continue
        time_str = span_time.get_text(strip=True)  # 例如 "2026年02月23日12时"
        
        # 2. 提取链接和标题
        a_tag = li.find('a', href=True)
        if not a_tag:
            continue
        title = a_tag.get_text(strip=True)
        href = a_tag['href']
        
        # 3. 补全链接（处理以 // 开头的相对地址）
        if href.startswith('//'):
            full_link = 'https:' + href
        elif href.startswith('/'):
            full_link = 'https://zjnews.zjol.com.cn' + href
        else:
            full_link = href
        
        # 4. 解析时间
        try:
            # 将 "2026年02月23日12时" 转换为 "2026-02-23 12"
            clean_time = time_str.replace('年', '-').replace('月', '-').replace('日', ' ').replace('时', '')
            pub_time = datetime.strptime(clean_time, "%Y-%m-%d %H")
            # 设置为东八区
            pub_time = pub_time.replace(tzinfo=pytz.timezone('Asia/Shanghai'))
        except Exception as e:
            print(f"时间解析失败: {time_str}，错误: {e}")
            continue
        
        articles.append({
            'title': title,
            'link': full_link,
            'pub_time': pub_time,
            'description': title  # 先用标题代替，可后续优化为抓取正文
        })
    
    # 按时间倒序排列（网页本身已倒序，但以防万一）
    articles.sort(key=lambda x: x['pub_time'], reverse=True)
    
    print(f"成功抓取到 {len(articles)} 篇文章")
    if articles:
        print(f"示例: {articles[0]['title']} - {articles[0]['pub_time']}")
    
    return articles[:MAX_ARTICLES]

def generate_rss(articles):
    """生成 RSS 2.0 文件"""
    if not articles:
        print("没有文章，不生成 RSS")
        return False
    
    fg = FeedGenerator()
    fg.title(BLOG_NAME)
    fg.link(href=BLOG_LINK, rel='alternate')
    fg.description(BLOG_DESCRIPTION)
    fg.language('zh-CN')
    
    for art in articles:
        fe = fg.add_entry()
        fe.title(art['title'])
        fe.link(href=art['link'])
        fe.description(art['description'])
        fe.pubDate(art['pub_time'])
        fe.guid(art['link'], permalink=True)  # 用链接作为唯一ID
    
    # 生成 RSS 文件
    fg.rss_file(OUTPUT_FILE, pretty=True)
    print(f"✅ RSS 文件已生成: {OUTPUT_FILE}")
    return True

if __name__ == "__main__":
    print("开始抓取浙江宣传文章...")
    articles = fetch_articles()
    if articles:
        generate_rss(articles)
        abs_path = os.path.abspath(OUTPUT_FILE)
        print(f"📁 文件保存路径: {abs_path}")
        print("你可以用 RSS 阅读器打开此文件测试")
    else:
        print("❌ 未能抓取到文章，请检查网络或网站是否改版")