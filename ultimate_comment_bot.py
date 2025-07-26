#!/usr/bin/env python3
"""
终极小红书评论机器人
使用最直接的方法解决评论输入框问题
"""

import asyncio
import json
import time
import random
from playwright.async_api import async_playwright
import os

class UltimateXiaohongshuBot:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.is_logged_in = False
        self.browser_data_dir = os.path.join(os.path.dirname(__file__), "ultimate_browser_data")
        os.makedirs(self.browser_data_dir, exist_ok=True)
        
    async def init_browser(self):
        """初始化浏览器"""
        print("🚀 初始化终极浏览器...")
        
        playwright = await async_playwright().start()
        
        self.context = await playwright.chromium.launch_persistent_context(
            user_data_dir=self.browser_data_dir,
            headless=False,
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ],
            timeout=120000
        )
        
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
            
        self.page.set_default_timeout(60000)
        
        print("✅ 终极浏览器初始化成功")
        
    async def login(self):
        """登录"""
        print("🔐 开始登录...")
        
        try:
            await self.page.goto("https://www.xiaohongshu.com", timeout=60000)
            await asyncio.sleep(3)
            
            # 检查登录状态
            login_buttons = await self.page.query_selector_all('text="登录"')
            if not login_buttons:
                self.is_logged_in = True
                print("✅ 已经登录")
                return True
                
            # 点击登录
            await login_buttons[0].click()
            await asyncio.sleep(2)
            
            print("📱 请在浏览器中完成登录...")
            
            # 等待登录
            for i in range(120):
                await asyncio.sleep(1)
                
                try:
                    current_login_buttons = await self.page.query_selector_all('text="登录"')
                    if not current_login_buttons:
                        self.is_logged_in = True
                        print("✅ 登录成功！")
                        return True
                except:
                    pass
                    
                if i % 10 == 0:
                    print(f"   等待中... ({i}s)")
            
            return False
            
        except Exception as e:
            print(f"❌ 登录出错: {e}")
            return False
    
    async def get_notes_from_search(self, keyword, limit=10):
        """从搜索页面获取笔记"""
        print(f"🔍 搜索: {keyword}")
        
        try:
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"
            await self.page.goto(search_url, timeout=60000)
            await asyncio.sleep(5)
            
            # 滚动加载
            for i in range(3):
                await self.page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(2)
            
            # 获取所有笔记链接
            notes = []
            links = await self.page.query_selector_all('a[href*="/search_result/"]')
            
            for link in links[:limit]:
                try:
                    href = await link.get_attribute('href')
                    if href and '/search_result/' in href:
                        # 获取标题
                        title = "未知标题"
                        try:
                            title_element = await link.query_selector('span, div, p')
                            if title_element:
                                title_text = await title_element.text_content()
                                if title_text and len(title_text.strip()) > 3:
                                    title = title_text.strip()[:50]
                        except:
                            pass
                        
                        notes.append({
                            'url': href,
                            'title': title
                        })
                except:
                    continue
            
            print(f"✅ 找到 {len(notes)} 个笔记")
            return notes
            
        except Exception as e:
            print(f"❌ 搜索出错: {e}")
            return []
    
    async def comment_with_direct_method(self, url, comment):
        """使用直接方法发布评论"""
        print(f"💬 直接评论: {url[:50]}...")
        
        try:
            # 访问页面
            await self.page.goto(url, timeout=60000)
            await asyncio.sleep(8)  # 增加等待时间
            
            # 检查页面有效性
            page_text = await self.page.text_content('body')
            if any(error in page_text for error in ["当前笔记暂时无法浏览", "内容不存在", "页面不存在"]):
                print("⚠️ 页面无效")
                return False
            
            print("📜 滚动到页面底部...")
            # 多次滚动确保页面完全加载
            for i in range(5):
                await self.page.evaluate(f"window.scrollTo(0, {i * 300})")
                await asyncio.sleep(1)
            
            # 滚动到底部
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(3)
            
            # 使用最直接的方法：模拟用户点击和输入
            print("🎯 尝试直接操作...")
            
            # 方法1: 查找并点击任何可能的评论区域
            comment_success = await self.page.evaluate(f"""
                async (comment) => {{
                    // 等待一下让页面稳定
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    
                    // 查找所有可能的评论输入元素
                    const possibleInputs = [
                        ...document.querySelectorAll('div[contenteditable="true"]'),
                        ...document.querySelectorAll('textarea'),
                        ...document.querySelectorAll('input[type="text"]'),
                        ...document.querySelectorAll('[placeholder*="说点什么"]'),
                        ...document.querySelectorAll('[placeholder*="评论"]')
                    ];
                    
                    console.log('找到可能的输入元素:', possibleInputs.length);
                    
                    for (const input of possibleInputs) {{
                        try {{
                            const rect = input.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {{
                                console.log('尝试输入元素:', input.tagName, input.className);
                                
                                // 滚动到元素位置
                                input.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                                await new Promise(resolve => setTimeout(resolve, 1000));
                                
                                // 点击元素
                                input.click();
                                input.focus();
                                await new Promise(resolve => setTimeout(resolve, 500));
                                
                                // 输入内容
                                if (input.tagName === 'DIV') {{
                                    input.textContent = comment;
                                    input.innerHTML = comment;
                                }} else {{
                                    input.value = comment;
                                }}
                                
                                // 触发事件
                                const events = ['input', 'change', 'keyup'];
                                for (const eventType of events) {{
                                    const event = new Event(eventType, {{ bubbles: true }});
                                    input.dispatchEvent(event);
                                }}
                                
                                await new Promise(resolve => setTimeout(resolve, 1000));
                                
                                // 查找发送按钮
                                const sendButtons = [
                                    ...Array.from(document.querySelectorAll('button')).filter(btn => 
                                        btn.textContent && (
                                            btn.textContent.includes('发送') || 
                                            btn.textContent.includes('发布') ||
                                            btn.textContent.includes('提交')
                                        )
                                    )
                                ];
                                
                                console.log('找到发送按钮:', sendButtons.length);
                                
                                if (sendButtons.length > 0) {{
                                    sendButtons[0].click();
                                    await new Promise(resolve => setTimeout(resolve, 2000));
                                    return {{ success: true, method: 'button_click' }};
                                }} else {{
                                    // 尝试回车键
                                    const enterEvent = new KeyboardEvent('keydown', {{
                                        key: 'Enter',
                                        code: 'Enter',
                                        keyCode: 13,
                                        bubbles: true
                                    }});
                                    input.dispatchEvent(enterEvent);
                                    await new Promise(resolve => setTimeout(resolve, 2000));
                                    return {{ success: true, method: 'enter_key' }};
                                }}
                            }}
                        }} catch (e) {{
                            console.error('输入元素操作失败:', e);
                            continue;
                        }}
                    }}
                    
                    return {{ success: false, reason: 'no_valid_input_found' }};
                }}
            """, comment)
            
            if comment_success.get('success'):
                print(f"✅ 评论成功 (方法: {comment_success.get('method')})")
                return True
            else:
                print(f"❌ 评论失败 (原因: {comment_success.get('reason')})")
                
                # 方法2: 尝试键盘输入
                print("🔄 尝试键盘输入方法...")
                try:
                    # 点击页面任意位置激活
                    await self.page.click('body')
                    await asyncio.sleep(1)
                    
                    # 使用Tab键导航到输入框
                    for _ in range(10):
                        await self.page.keyboard.press('Tab')
                        await asyncio.sleep(0.5)
                        
                        # 尝试输入
                        await self.page.keyboard.type(comment)
                        await asyncio.sleep(1)
                        await self.page.keyboard.press('Enter')
                        await asyncio.sleep(2)
                        
                        # 检查是否成功
                        current_text = await self.page.text_content('body')
                        if comment in current_text:
                            print("✅ 键盘输入成功")
                            return True
                        
                        # 清除输入的内容
                        await self.page.keyboard.press('Control+a')
                        await self.page.keyboard.press('Delete')
                        
                except Exception as e:
                    print(f"键盘输入失败: {e}")
                
                return False
                
        except Exception as e:
            print(f"❌ 评论过程出错: {e}")
            return False
    
    async def run_ultimate_task(self):
        """运行终极评论任务"""
        print("🎯 启动终极小红书评论机器人")
        print("=" * 60)
        
        try:
            # 初始化
            await self.init_browser()
            
            # 登录
            if not await self.login():
                print("❌ 登录失败")
                return
            
            # 获取笔记
            notes = await self.get_notes_from_search("全屋定制", 10)
            if not notes:
                print("❌ 未找到笔记")
                return
            
            print(f"📝 开始处理 {len(notes)} 个笔记...")
            
            # 发布评论
            success_count = 0
            for i, note in enumerate(notes, 1):
                print(f"\n📌 [{i}/{len(notes)}] {note['title']}")
                
                # 等待
                wait_time = random.uniform(20, 30)
                print(f"⏳ 等待 {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                
                # 评论
                if await self.comment_with_direct_method(note['url'], "我自荐，可以看看我的主页"):
                    success_count += 1
                    print(f"✅ 成功 [{success_count}/{i}]")
                else:
                    print(f"❌ 失败 [{success_count}/{i}]")
                
                # 每2个笔记休息
                if i % 2 == 0 and i < len(notes):
                    rest_time = random.uniform(90, 120)
                    print(f"😴 长休息 {rest_time:.1f}s...")
                    await asyncio.sleep(rest_time)
            
            print("\n" + "=" * 60)
            print(f"🎉 终极任务完成！")
            print(f"📊 最终成功率: {success_count}/{len(notes)} ({success_count/len(notes)*100:.1f}%)")
            
        except Exception as e:
            print(f"❌ 任务执行出错: {e}")
        
        print("🔚 浏览器保持打开状态")

async def main():
    bot = UltimateXiaohongshuBot()
    await bot.run_ultimate_task()

if __name__ == "__main__":
    asyncio.run(main())