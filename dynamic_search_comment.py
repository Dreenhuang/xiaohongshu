#!/usr/bin/env python3
"""
动态搜索评论机器人
每次都重新搜索"全屋定制"关键词，获取最新的笔记进行评论
"""

import asyncio
import time
import random
from playwright.async_api import async_playwright
import os

class DynamicSearchCommentBot:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.browser_data_dir = os.path.join(os.path.dirname(__file__), "dynamic_browser_data")
        os.makedirs(self.browser_data_dir, exist_ok=True)
        
    async def init_browser(self):
        """初始化浏览器"""
        print("🚀 初始化动态搜索浏览器...")
        
        try:
            if self.playwright:
                await self.playwright.stop()
        except:
            pass
            
        self.playwright = await async_playwright().start()
        
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.browser_data_dir,
            headless=False,
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ],
            timeout=120000
        )
        
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
            
        self.page.set_default_timeout(30000)
        print("✅ 浏览器初始化成功")
        
    async def check_login(self):
        """检查登录状态"""
        print("🔐 检查登录状态...")
        
        try:
            await self.page.goto("https://www.xiaohongshu.com", timeout=30000)
            await asyncio.sleep(3)
            
            # 检查登录按钮
            login_buttons = await self.page.query_selector_all('text="登录"')
            if login_buttons:
                print("❌ 需要登录，请在浏览器中完成登录后按回车...")
                input()
                
                await self.page.reload()
                await asyncio.sleep(2)
                login_buttons = await self.page.query_selector_all('text="登录"')
                if login_buttons:
                    return False
            
            print("✅ 登录状态正常")
            return True
            
        except Exception as e:
            print(f"❌ 登录检查失败: {e}")
            return False
    
    async def search_and_get_notes(self, keyword="全屋定制", limit=10):
        """动态搜索并获取笔记"""
        print(f"🔍 动态搜索关键词: {keyword}")
        
        try:
            # 访问小红书首页
            await self.page.goto("https://www.xiaohongshu.com", timeout=30000)
            await asyncio.sleep(3)
            
            # 查找搜索框并输入关键词
            print("📝 在搜索框输入关键词...")
            search_input = await self.page.wait_for_selector('input[placeholder*="搜索"], input[type="search"], input[class*="search"]', timeout=10000)
            
            if search_input:
                await search_input.click()
                await search_input.fill("")  # 清空
                await search_input.type(keyword)
                await asyncio.sleep(1)
                
                # 按回车搜索
                await self.page.keyboard.press('Enter')
                await asyncio.sleep(5)
                
                print("✅ 搜索完成，获取笔记列表...")
                
                # 滚动加载更多内容
                for i in range(3):
                    await self.page.evaluate("window.scrollBy(0, 800)")
                    await asyncio.sleep(2)
                
                # 获取笔记链接
                notes = []
                
                # 查找笔记链接
                note_links = await self.page.query_selector_all('a[href*="/explore/"]')
                
                print(f"🔗 找到 {len(note_links)} 个笔记链接")
                
                for i, link in enumerate(note_links[:limit]):
                    try:
                        href = await link.get_attribute('href')
                        if href and '/explore/' in href:
                            # 获取标题
                            title = f"笔记 {i+1}"
                            try:
                                title_element = await link.query_selector('span, div, p')
                                if title_element:
                                    title_text = await title_element.text_content()
                                    if title_text and len(title_text.strip()) > 3:
                                        title = title_text.strip()[:50]
                            except:
                                pass
                            
                            full_url = href if href.startswith('http') else f"https://www.xiaohongshu.com{href}"
                            notes.append({
                                'url': full_url,
                                'title': title
                            })
                    except:
                        continue
                
                print(f"✅ 成功获取 {len(notes)} 个笔记")
                return notes
            else:
                print("❌ 未找到搜索框")
                return []
                
        except Exception as e:
            print(f"❌ 搜索过程出错: {e}")
            return []
    
    async def find_comment_input_simple(self, comment_text):
        """简化的评论输入框查找"""
        print('🔍 查找评论输入框...')
        
        try:
            # 等待页面加载完成
            await asyncio.sleep(3)
            
            # 滚动到页面底部
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(3)
            
            # 查找包含"说点什么"的元素
            say_elements = await self.page.query_selector_all('*:has-text("说点什么")')
            
            if say_elements:
                print(f"找到 {len(say_elements)} 个'说点什么'元素")
                
                for say_el in say_elements:
                    try:
                        # 在该元素附近查找输入框
                        input_selectors = [
                            'textarea',
                            'input[type="text"]',
                            'div[contenteditable="true"]'
                        ]
                        
                        for selector in input_selectors:
                            inputs = await say_el.query_selector_all(selector)
                            if not inputs:
                                # 在父元素中查找
                                parent = await say_el.query_selector('..')
                                if parent:
                                    inputs = await parent.query_selector_all(selector)
                            
                            for input_el in inputs:
                                try:
                                    # 检查元素是否可见
                                    is_visible = await input_el.is_visible()
                                    if is_visible:
                                        print(f"找到可见的输入框: {selector}")
                                        
                                        # 滚动到输入框
                                        await input_el.scroll_into_view_if_needed()
                                        await asyncio.sleep(1)
                                        
                                        # 点击并输入
                                        await input_el.click()
                                        await input_el.fill(comment_text)
                                        await asyncio.sleep(1)
                                        
                                        # 查找发送按钮
                                        send_buttons = await self.page.query_selector_all('button:has-text("发送"), button:has-text("发布")')
                                        if send_buttons:
                                            await send_buttons[0].click()
                                            print("✅ 点击发送按钮")
                                        else:
                                            # 尝试回车
                                            await self.page.keyboard.press('Enter')
                                            print("✅ 按回车发送")
                                        
                                        return True
                                        
                                except Exception as e:
                                    print(f"操作输入框失败: {e}")
                                    continue
                    except Exception as e:
                        print(f"处理'说点什么'元素失败: {e}")
                        continue
            
            # 如果没找到"说点什么"，尝试直接查找输入框
            print("未找到'说点什么'，尝试直接查找输入框...")
            
            input_selectors = [
                'textarea[placeholder*="评论"]',
                'textarea[placeholder*="说点什么"]',
                'input[placeholder*="评论"]',
                'input[placeholder*="说点什么"]',
                'div[contenteditable="true"]'
            ]
            
            for selector in input_selectors:
                try:
                    inputs = await self.page.query_selector_all(selector)
                    for input_el in inputs:
                        is_visible = await input_el.is_visible()
                        if is_visible:
                            print(f"找到输入框: {selector}")
                            await input_el.scroll_into_view_if_needed()
                            await input_el.click()
                            await input_el.fill(comment_text)
                            
                            # 尝试发送
                            send_buttons = await self.page.query_selector_all('button:has-text("发送"), button:has-text("发布")')
                            if send_buttons:
                                await send_buttons[0].click()
                            else:
                                await self.page.keyboard.press('Enter')
                            
                            return True
                except Exception as e:
                    print(f"操作 {selector} 失败: {e}")
                    continue
            
            return False
            
        except Exception as e:
            print(f"❌ 查找评论输入框失败: {e}")
            return False
    
    async def comment_on_note(self, note_url, comment_text, title):
        """对单个笔记进行评论"""
        print(f"💬 评论笔记: {title}")
        
        try:
            # 访问笔记页面
            await self.page.goto(note_url, timeout=30000)
            await asyncio.sleep(5)
            
            # 检查页面是否有效
            page_content = await self.page.content()
            if "当前笔记暂时无法浏览" in page_content or "内容不存在" in page_content:
                print("⚠️ 笔记无法访问")
                return False
            
            # 查找并操作评论输入框
            success = await self.find_comment_input_simple(comment_text)
            
            if success:
                print("✅ 评论发布成功")
                await asyncio.sleep(3)
                return True
            else:
                print("❌ 自动评论失败")
                print(f"💬 请手动添加评论: {comment_text}")
                print("✅ 完成后按回车继续...")
                input()
                return True
                
        except Exception as e:
            print(f"❌ 评论过程出错: {e}")
            return False
    
    async def run_dynamic_task(self, target_count=10):
        """运行动态搜索评论任务"""
        print("🎯 启动动态搜索评论机器人")
        print("=" * 60)
        
        try:
            # 初始化浏览器
            await self.init_browser()
            
            # 检查登录
            if not await self.check_login():
                print("❌ 登录失败")
                return
            
            success_count = 0
            
            for round_num in range(1, target_count + 1):
                print(f"\n🔄 第 {round_num} 轮评论")
                print("-" * 40)
                
                # 每次都重新搜索获取新的笔记
                notes = await self.search_and_get_notes("全屋定制", 5)  # 每次获取5个笔记
                
                if not notes:
                    print("❌ 未获取到笔记，跳过本轮")
                    continue
                
                # 随机选择一个笔记进行评论
                selected_note = random.choice(notes)
                print(f"🎯 选中笔记: {selected_note['title']}")
                
                # 等待
                wait_time = random.uniform(10, 20)
                print(f"⏳ 等待 {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                
                # 评论
                if await self.comment_on_note(selected_note['url'], "我自荐，可以看看我的主页", selected_note['title']):
                    success_count += 1
                    print(f"✅ 成功 [{success_count}/{round_num}]")
                else:
                    print(f"❌ 失败 [{success_count}/{round_num}]")
                
                # 每3轮休息一下
                if round_num % 3 == 0 and round_num < target_count:
                    rest_time = random.uniform(60, 90)
                    print(f"😴 休息 {rest_time:.1f}s...")
                    await asyncio.sleep(rest_time)
            
            print("\n" + "=" * 60)
            print(f"🎉 动态搜索任务完成！")
            print(f"📊 最终成功率: {success_count}/{target_count} ({success_count/target_count*100:.1f}%)")
            
        except Exception as e:
            print(f"❌ 任务执行出错: {e}")
        finally:
            print("🔚 浏览器保持打开状态")

async def main():
    bot = DynamicSearchCommentBot()
    await bot.run_dynamic_task(10)  # 执行10轮评论

if __name__ == "__main__":
    asyncio.run(main())