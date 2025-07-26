#!/usr/bin/env python3
"""
稳定的小红书自动评论脚本
解决浏览器会话关闭问题
"""

import asyncio
import json
import time
import random
from playwright.async_api import async_playwright
import os

class StableXiaohongshuBot:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.is_logged_in = False
        self.browser_data_dir = os.path.join(os.path.dirname(__file__), "stable_browser_data")
        os.makedirs(self.browser_data_dir, exist_ok=True)
        
    async def init_browser(self):
        """初始化浏览器，使用更稳定的配置"""
        print("🚀 初始化浏览器...")
        
        playwright = await async_playwright().start()
        
        # 使用更隐蔽的浏览器配置
        self.context = await playwright.chromium.launch_persistent_context(
            user_data_dir=self.browser_data_dir,
            headless=False,  # 显示浏览器窗口
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions-except',
                '--disable-plugins-discovery',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-default-apps',
                '--disable-popup-blocking'
            ],
            timeout=120000  # 增加超时时间
        )
        
        # 获取或创建页面
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
            
        # 设置页面超时
        self.page.set_default_timeout(60000)
        
        # 注入反检测脚本
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en'],
            });
            
            window.chrome = {
                runtime: {},
            };
        """)
        
        print("✅ 浏览器初始化成功")
        
    async def login_with_retry(self, max_retries=3):
        """带重试的登录功能"""
        for attempt in range(max_retries):
            try:
                print(f"🔐 尝试登录小红书 (第{attempt + 1}次)...")
                
                await self.page.goto("https://www.xiaohongshu.com", timeout=60000)
                await asyncio.sleep(3)
                
                # 检查是否已登录
                login_buttons = await self.page.query_selector_all('text="登录"')
                if not login_buttons:
                    self.is_logged_in = True
                    print("✅ 已经登录小红书")
                    return True
                    
                # 点击登录按钮
                await login_buttons[0].click()
                await asyncio.sleep(2)
                
                print("⏳ 请在浏览器中完成登录...")
                print("   - 可以使用手机扫码登录")
                print("   - 或者输入账号密码登录")
                print("   - 登录完成后脚本将自动继续")
                
                # 等待登录完成
                for wait_time in range(180):  # 等待3分钟
                    await asyncio.sleep(1)
                    
                    # 检查是否登录成功
                    try:
                        current_login_buttons = await self.page.query_selector_all('text="登录"')
                        if not current_login_buttons:
                            self.is_logged_in = True
                            print("✅ 登录成功！")
                            return True
                    except:
                        pass
                        
                    if wait_time % 10 == 0:
                        print(f"   等待登录中... ({wait_time}s)")
                
                print("⚠️ 登录超时，重试...")
                
            except Exception as e:
                print(f"❌ 登录尝试失败: {e}")
                if attempt < max_retries - 1:
                    print("🔄 重新初始化浏览器...")
                    await self.reinit_browser()
                    
        return False
        
    async def reinit_browser(self):
        """重新初始化浏览器"""
        try:
            if self.context:
                await self.context.close()
        except:
            pass
            
        await asyncio.sleep(2)
        await self.init_browser()
        
    async def search_notes_stable(self, keyword, limit=10):
        """稳定的搜索笔记功能"""
        print(f"🔍 搜索关键词: {keyword}")
        
        try:
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"
            await self.page.goto(search_url, timeout=60000)
            await asyncio.sleep(5)
            
            # 滚动加载更多内容
            for i in range(3):
                await self.page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(2)
            
            # 获取笔记链接
            notes = []
            
            # 尝试多种选择器
            selectors = [
                'a[href*="/search_result/"]',
                'section.note-item a',
                'div[data-v-a264b01a] a'
            ]
            
            for selector in selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    print(f"使用选择器 {selector} 找到 {len(elements)} 个元素")
                    
                    for element in elements[:limit]:
                        try:
                            href = await element.get_attribute('href')
                            if href and '/search_result/' in href:
                                if href.startswith('/'):
                                    full_url = f"https://www.xiaohongshu.com{href}"
                                else:
                                    full_url = href
                                    
                                # 尝试获取标题
                                title = "未知标题"
                                try:
                                    title_element = await element.query_selector('span, div')
                                    if title_element:
                                        title_text = await title_element.text_content()
                                        if title_text and len(title_text.strip()) > 3:
                                            title = title_text.strip()
                                except:
                                    pass
                                
                                notes.append({
                                    'url': full_url,
                                    'title': title
                                })
                                
                        except Exception as e:
                            print(f"处理单个元素时出错: {e}")
                            continue
                    
                    if notes:
                        break
                        
                except Exception as e:
                    print(f"使用选择器 {selector} 时出错: {e}")
                    continue
            
            # 去重
            unique_notes = []
            seen_urls = set()
            for note in notes:
                if note['url'] not in seen_urls:
                    seen_urls.add(note['url'])
                    unique_notes.append(note)
            
            print(f"✅ 找到 {len(unique_notes)} 个唯一笔记")
            return unique_notes[:limit]
            
        except Exception as e:
            print(f"❌ 搜索笔记时出错: {e}")
            return []
    
    async def post_comment_stable(self, url, comment, max_retries=3):
        """稳定的评论发布功能"""
        for attempt in range(max_retries):
            try:
                print(f"💬 发布评论到: {url[:50]}... (第{attempt + 1}次尝试)")
                
                # 访问笔记页面
                await self.page.goto(url, timeout=60000)
                await asyncio.sleep(random.uniform(5, 8))  # 增加等待时间
                
                # 检查页面是否正常加载
                page_text = await self.page.text_content('body')
                if "当前笔记暂时无法浏览" in page_text or "内容不存在" in page_text:
                    print("⚠️ 笔记无法访问，跳过")
                    return False
                
                # 多次滚动，确保页面完全加载
                print("📜 滚动页面加载内容...")
                for i in range(5):
                    await self.page.evaluate(f"window.scrollTo(0, {i * 500})")
                    await asyncio.sleep(1)
                
                # 滚动到底部
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(3)
                
                # 打印页面信息用于调试
                print("🔍 分析页面结构...")
                page_info = await self.page.evaluate("""
                    () => {
                        const editableElements = document.querySelectorAll('[contenteditable="true"]');
                        const textareas = document.querySelectorAll('textarea');
                        const inputs = document.querySelectorAll('input[type="text"]');
                        const commentTexts = Array.from(document.querySelectorAll('*')).filter(el => 
                            el.textContent && (el.textContent.includes('说点什么') || el.textContent.includes('评论'))
                        );
                        
                        return {
                            editableCount: editableElements.length,
                            textareaCount: textareas.length,
                            inputCount: inputs.length,
                            commentTextCount: commentTexts.length,
                            hasCommentSection: document.querySelector('.comment-container, .comments-container, .comment-list') !== null,
                            bodyText: document.body.textContent.slice(0, 500)
                        };
                    }
                """)
                print(f"页面分析: {page_info}")
                
                # 扩展的评论输入框选择器
                comment_input = None
                input_selectors = [
                    'div[contenteditable="true"]',
                    'textarea[placeholder*="说点什么"]',
                    'div[placeholder*="说点什么"]',
                    'textarea[placeholder*="评论"]',
                    'div[placeholder*="评论"]',
                    'textarea',
                    'input[type="text"]',
                    '[data-testid="comment-input"]',
                    '.comment-input',
                    '.input-box textarea',
                    '.comment-box textarea'
                ]
                
                # 尝试查找输入框
                for selector in input_selectors:
                    try:
                        elements = await self.page.query_selector_all(selector)
                        print(f"选择器 {selector} 找到 {len(elements)} 个元素")
                        
                        for element in elements:
                            try:
                                if await element.is_visible():
                                    # 检查元素是否可能是评论输入框
                                    placeholder = await element.get_attribute('placeholder') or ""
                                    class_name = await element.get_attribute('class') or ""
                                    
                                    if any(keyword in placeholder.lower() for keyword in ['说点什么', '评论', 'comment']) or \
                                       any(keyword in class_name.lower() for keyword in ['comment', 'input']):
                                        comment_input = element
                                        print(f"✅ 找到可能的评论输入框: {selector}")
                                        break
                                    elif selector in ['textarea', 'input[type="text"]'] and not placeholder:
                                        # 如果是通用输入框且没有placeholder，也尝试使用
                                        comment_input = element
                                        print(f"✅ 找到通用输入框: {selector}")
                                        break
                            except:
                                continue
                        
                        if comment_input:
                            break
                    except Exception as e:
                        print(f"选择器 {selector} 出错: {e}")
                        continue
                
                # 如果还是没找到，尝试点击可能的评论区域
                if not comment_input:
                    print("🔍 尝试激活评论输入框...")
                    click_targets = [
                        'text="说点什么"',
                        'text="评论"',
                        'text="写评论"',
                        '.comment-placeholder',
                        '.comment-trigger'
                    ]
                    
                    for target in click_targets:
                        try:
                            element = await self.page.query_selector(target)
                            if element and await element.is_visible():
                                await element.click()
                                await asyncio.sleep(2)
                                print(f"✅ 点击了: {target}")
                                
                                # 再次查找输入框
                                for selector in input_selectors[:5]:  # 只检查主要选择器
                                    try:
                                        new_element = await self.page.query_selector(selector)
                                        if new_element and await new_element.is_visible():
                                            comment_input = new_element
                                            print(f"✅ 激活后找到输入框: {selector}")
                                            break
                                    except:
                                        continue
                                
                                if comment_input:
                                    break
                        except Exception as e:
                            print(f"点击 {target} 出错: {e}")
                            continue
                
                if not comment_input:
                    print("❌ 未找到评论输入框")
                    if attempt < max_retries - 1:
                        print("🔄 等待后重试...")
                        await asyncio.sleep(10)
                        continue
                    return False
                
                # 输入评论
                await comment_input.click()
                await asyncio.sleep(1)
                
                # 清空输入框并输入新内容
                await self.page.keyboard.press("Control+a")
                await asyncio.sleep(0.5)
                await self.page.keyboard.type(comment)
                await asyncio.sleep(1)
                
                # 发送评论
                send_success = False
                
                # 方法1: 查找发送按钮
                try:
                    send_button = await self.page.query_selector('button:has-text("发送")')
                    if send_button and await send_button.is_visible():
                        await send_button.click()
                        send_success = True
                except:
                    pass
                
                # 方法2: 使用回车键
                if not send_success:
                    try:
                        await self.page.keyboard.press("Enter")
                        send_success = True
                    except:
                        pass
                
                # 方法3: JavaScript点击
                if not send_success:
                    try:
                        await self.page.evaluate("""
                            () => {
                                const buttons = Array.from(document.querySelectorAll('button'));
                                const sendBtn = buttons.find(btn => btn.textContent.includes('发送'));
                                if (sendBtn) {
                                    sendBtn.click();
                                    return true;
                                }
                                return false;
                            }
                        """)
                        send_success = True
                    except:
                        pass
                
                if send_success:
                    await asyncio.sleep(2)
                    print("✅ 评论发布成功")
                    return True
                else:
                    print("❌ 评论发布失败")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                        continue
                    return False
                    
            except Exception as e:
                print(f"❌ 发布评论时出错: {e}")
                if attempt < max_retries - 1:
                    print("🔄 重试中...")
                    await asyncio.sleep(5)
                    continue
                return False
        
        return False
    
    async def run_auto_comment(self, keyword="全屋定制", comment="我自荐，可以看看我的主页", limit=10):
        """运行自动评论任务"""
        print("🌸 开始小红书自动评论任务")
        print("=" * 50)
        
        try:
            # 初始化浏览器
            await self.init_browser()
            
            # 登录
            if not await self.login_with_retry():
                print("❌ 登录失败，无法继续")
                return
            
            # 搜索笔记
            notes = await self.search_notes_stable(keyword, limit)
            if not notes:
                print("❌ 未找到笔记，任务结束")
                return
            
            print(f"📝 找到 {len(notes)} 个笔记，开始评论...")
            
            # 逐个评论
            success_count = 0
            for i, note in enumerate(notes, 1):
                print(f"\n📌 处理第 {i}/{len(notes)} 个笔记")
                print(f"标题: {note['title']}")
                
                # 随机等待，避免被检测
                wait_time = random.uniform(10, 20)
                print(f"⏳ 等待 {wait_time:.1f} 秒...")
                await asyncio.sleep(wait_time)
                
                # 发布评论
                if await self.post_comment_stable(note['url'], comment):
                    success_count += 1
                    print(f"✅ 成功 {success_count}/{i}")
                else:
                    print(f"❌ 失败 {success_count}/{i}")
                
                # 每5个笔记后长时间休息
                if i % 5 == 0 and i < len(notes):
                    rest_time = random.uniform(60, 120)
                    print(f"😴 长时间休息 {rest_time:.1f} 秒...")
                    await asyncio.sleep(rest_time)
            
            print("\n" + "=" * 50)
            print(f"🎉 任务完成！")
            print(f"📊 成功率: {success_count}/{len(notes)} ({success_count/len(notes)*100:.1f}%)")
            
        except Exception as e:
            print(f"❌ 任务执行出错: {e}")
        finally:
            print("🔚 保持浏览器打开，您可以手动检查结果")
            # 不关闭浏览器，让用户检查结果

async def main():
    bot = StableXiaohongshuBot()
    await bot.run_auto_comment(
        keyword="全屋定制",
        comment="我自荐，可以看看我的主页",
        limit=10
    )

if __name__ == "__main__":
    asyncio.run(main())