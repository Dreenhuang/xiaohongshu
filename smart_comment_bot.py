#!/usr/bin/env python3
"""
智能小红书评论机器人
自适应页面结构，解决评论输入框识别问题
"""

import asyncio
import json
import time
import random
from playwright.async_api import async_playwright
import os

class SmartXiaohongshuBot:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.is_logged_in = False
        self.browser_data_dir = os.path.join(os.path.dirname(__file__), "smart_browser_data")
        os.makedirs(self.browser_data_dir, exist_ok=True)
        
    async def init_browser(self):
        """初始化浏览器"""
        print("🚀 初始化智能浏览器...")
        
        playwright = await async_playwright().start()
        
        self.context = await playwright.chromium.launch_persistent_context(
            user_data_dir=self.browser_data_dir,
            headless=False,
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-web-security'
            ],
            timeout=120000
        )
        
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
            
        self.page.set_default_timeout(60000)
        
        # 注入智能脚本
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // 添加智能评论输入框检测函数
            window.findCommentInput = function() {
                // 按优先级查找评论输入框
                const selectors = [
                    'div[contenteditable="true"]',
                    'textarea[placeholder*="说点什么"]',
                    'textarea[placeholder*="评论"]',
                    'div[placeholder*="说点什么"]',
                    'textarea',
                    'input[type="text"]'
                ];
                
                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    for (const el of elements) {
                        if (el.offsetParent !== null) { // 检查元素是否可见
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                const placeholder = el.placeholder || '';
                                const className = el.className || '';
                                
                                // 检查是否是评论相关的输入框
                                if (placeholder.includes('说点什么') || 
                                    placeholder.includes('评论') ||
                                    className.includes('comment') ||
                                    selector === 'div[contenteditable="true"]') {
                                    return el;
                                }
                            }
                        }
                    }
                }
                return null;
            };
            
            // 智能点击评论区域
            window.activateCommentArea = function() {
                const triggers = [
                    '说点什么',
                    '评论',
                    '写评论',
                    '发表评论'
                ];
                
                for (const trigger of triggers) {
                    const elements = Array.from(document.querySelectorAll('*')).filter(el => 
                        el.textContent && el.textContent.includes(trigger) && 
                        el.offsetParent !== null
                    );
                    
                    if (elements.length > 0) {
                        elements[0].click();
                        return true;
                    }
                }
                return false;
            };
        """)
        
        print("✅ 智能浏览器初始化成功")
        
    async def smart_login(self):
        """智能登录"""
        print("🔐 开始智能登录...")
        
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
            
            print("📱 请在浏览器中完成登录（扫码或密码）...")
            
            # 智能等待登录
            for i in range(180):
                await asyncio.sleep(1)
                
                try:
                    current_login_buttons = await self.page.query_selector_all('text="登录"')
                    if not current_login_buttons:
                        self.is_logged_in = True
                        print("✅ 登录成功！")
                        return True
                except:
                    pass
                    
                if i % 15 == 0:
                    print(f"   等待中... ({i}s)")
            
            print("⚠️ 登录超时")
            return False
            
        except Exception as e:
            print(f"❌ 登录出错: {e}")
            return False
    
    async def smart_search(self, keyword, limit=10):
        """智能搜索"""
        print(f"🔍 智能搜索: {keyword}")
        
        try:
            # 方法1: 直接访问搜索URL
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"
            await self.page.goto(search_url, timeout=60000)
            await asyncio.sleep(5)
            
            # 滚动加载
            for i in range(3):
                await self.page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(2)
            
            # 智能提取笔记链接
            notes = await self.page.evaluate(f"""
                () => {{
                    const notes = [];
                    const links = Array.from(document.querySelectorAll('a[href*="/search_result/"]'));
                    
                    for (const link of links.slice(0, {limit})) {{
                        const href = link.href;
                        if (href && href.includes('/search_result/')) {{
                            // 尝试获取标题
                            let title = '未知标题';
                            const titleEl = link.querySelector('span, div, p');
                            if (titleEl && titleEl.textContent.trim()) {{
                                title = titleEl.textContent.trim();
                            }}
                            
                            notes.push({{
                                url: href,
                                title: title
                            }});
                        }}
                    }}
                    
                    return notes;
                }}
            """)
            
            print(f"✅ 找到 {len(notes)} 个笔记")
            return notes
            
        except Exception as e:
            print(f"❌ 搜索出错: {e}")
            return []
    
    async def smart_comment(self, url, comment):
        """智能评论发布"""
        print(f"💬 智能评论: {url[:50]}...")
        
        try:
            # 访问页面
            await self.page.goto(url, timeout=60000)
            await asyncio.sleep(5)
            
            # 检查页面有效性
            page_text = await self.page.text_content('body')
            if any(error in page_text for error in ["当前笔记暂时无法浏览", "内容不存在", "页面不存在"]):
                print("⚠️ 页面无效，跳过")
                return False
            
            # 智能滚动到评论区
            print("📜 定位评论区...")
            await self.page.evaluate("""
                () => {
                    // 查找评论相关元素并滚动到该位置
                    const commentKeywords = ['评论', '条评论', '说点什么'];
                    for (const keyword of commentKeywords) {
                        const elements = Array.from(document.querySelectorAll('*')).filter(el => 
                            el.textContent && el.textContent.includes(keyword)
                        );
                        if (elements.length > 0) {
                            elements[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
                            return true;
                        }
                    }
                    // 如果没找到，滚动到底部
                    window.scrollTo(0, document.body.scrollHeight);
                    return false;
                }
            """)
            await asyncio.sleep(3)
            
            # 使用智能函数查找输入框
            print("🔍 智能查找评论输入框...")
            input_found = await self.page.evaluate("""
                () => {
                    const input = window.findCommentInput();
                    if (input) {
                        input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        return true;
                    }
                    return false;
                }
            """)
            
            if not input_found:
                # 尝试激活评论区
                print("🔄 尝试激活评论区...")
                activated = await self.page.evaluate("() => window.activateCommentArea()")
                if activated:
                    await asyncio.sleep(2)
                    input_found = await self.page.evaluate("() => window.findCommentInput() !== null")
            
            if not input_found:
                print("❌ 无法找到评论输入框")
                return False
            
            # 点击并输入评论
            print("✍️ 输入评论内容...")
            success = await self.page.evaluate(f"""
                (comment) => {{
                    const input = window.findCommentInput();
                    if (!input) return false;
                    
                    try {{
                        // 点击输入框
                        input.click();
                        input.focus();
                        
                        // 清空并输入内容
                        if (input.tagName === 'DIV') {{
                            input.innerHTML = '';
                            input.textContent = comment;
                        }} else {{
                            input.value = '';
                            input.value = comment;
                        }}
                        
                        // 触发输入事件
                        const inputEvent = new Event('input', {{ bubbles: true }});
                        input.dispatchEvent(inputEvent);
                        
                        return true;
                    }} catch (e) {{
                        console.error('输入评论出错:', e);
                        return false;
                    }}
                }}
            """, comment)
            
            if not success:
                print("❌ 输入评论失败")
                return False
            
            await asyncio.sleep(2)
            
            # 智能发送评论
            print("📤 发送评论...")
            sent = await self.page.evaluate("""
                () => {
                    // 查找发送按钮
                    const sendSelectors = [
                        'button:has-text("发送")',
                        'button:has-text("发布")',
                        'button:has-text("提交")',
                        'button[type="submit"]'
                    ];
                    
                    for (const selector of sendSelectors) {
                        try {
                            const buttons = Array.from(document.querySelectorAll('button')).filter(btn => 
                                btn.textContent && (
                                    btn.textContent.includes('发送') || 
                                    btn.textContent.includes('发布') ||
                                    btn.textContent.includes('提交')
                                )
                            );
                            
                            if (buttons.length > 0) {
                                buttons[0].click();
                                return true;
                            }
                        } catch (e) {
                            continue;
                        }
                    }
                    
                    return false;
                }
            """)
            
            if not sent:
                # 尝试回车键
                await self.page.keyboard.press("Enter")
                sent = True
            
            if sent:
                await asyncio.sleep(2)
                print("✅ 评论发送成功")
                return True
            else:
                print("❌ 评论发送失败")
                return False
                
        except Exception as e:
            print(f"❌ 评论过程出错: {e}")
            return False
    
    async def run_smart_comment_task(self):
        """运行智能评论任务"""
        print("🤖 启动智能小红书评论机器人")
        print("=" * 60)
        
        try:
            # 初始化
            await self.init_browser()
            
            # 登录
            if not await self.smart_login():
                print("❌ 登录失败")
                return
            
            # 搜索笔记
            notes = await self.smart_search("全屋定制", 10)
            if not notes:
                print("❌ 未找到笔记")
                return
            
            print(f"📝 开始处理 {len(notes)} 个笔记...")
            
            # 智能评论
            success_count = 0
            for i, note in enumerate(notes, 1):
                print(f"\n📌 [{i}/{len(notes)}] {note['title'][:30]}...")
                
                # 智能等待
                wait_time = random.uniform(15, 25)
                print(f"⏳ 智能等待 {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                
                # 发布评论
                if await self.smart_comment(note['url'], "我自荐，可以看看我的主页"):
                    success_count += 1
                    print(f"✅ 成功 [{success_count}/{i}]")
                else:
                    print(f"❌ 失败 [{success_count}/{i}]")
                
                # 每3个笔记休息
                if i % 3 == 0 and i < len(notes):
                    rest_time = random.uniform(60, 90)
                    print(f"😴 智能休息 {rest_time:.1f}s...")
                    await asyncio.sleep(rest_time)
            
            print("\n" + "=" * 60)
            print(f"🎉 智能任务完成！")
            print(f"📊 最终成功率: {success_count}/{len(notes)} ({success_count/len(notes)*100:.1f}%)")
            
        except Exception as e:
            print(f"❌ 任务执行出错: {e}")
        
        print("🔚 浏览器保持打开，可手动检查结果")

async def main():
    bot = SmartXiaohongshuBot()
    await bot.run_smart_comment_task()

if __name__ == "__main__":
    asyncio.run(main())