#!/usr/bin/env python3
"""
稳定的小红书评论机器人 - 专门查找"说点什么"评论框
自动处理浏览器会话关闭问题
"""

import asyncio
import json
import time
import random
from playwright.async_api import async_playwright
import os

class StableCommentBot:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.browser_data_dir = os.path.join(os.path.dirname(__file__), "stable_browser_data")
        os.makedirs(self.browser_data_dir, exist_ok=True)
        
    async def init_browser(self):
        """初始化浏览器"""
        print("🚀 初始化稳定浏览器...")
        
        try:
            if self.playwright:
                await self.playwright.stop()
        except:
            pass
            
        self.playwright = await async_playwright().start()
        
        # 使用持久化上下文，保持登录状态
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.browser_data_dir,
            headless=False,
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ],
            timeout=120000
        )
        
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
            
        self.page.set_default_timeout(60000)
        
        print("✅ 稳定浏览器初始化成功")
        return True
        
    async def check_browser_health(self):
        """检查浏览器健康状态"""
        try:
            if not self.page or self.page.is_closed():
                return False
            await self.page.evaluate("1 + 1")
            return True
        except:
            return False
    
    async def ensure_browser_ready(self):
        """确保浏览器准备就绪"""
        if not await self.check_browser_health():
            print("🔄 浏览器会话已断开，重新初始化...")
            await self.init_browser()
            await self.quick_login_check()
        
    async def quick_login_check(self):
        """快速登录检查"""
        print("🔐 检查登录状态...")
        
        try:
            await self.page.goto("https://www.xiaohongshu.com", timeout=60000)
            await asyncio.sleep(3)
            
            # 检查是否有登录按钮
            login_buttons = await self.page.query_selector_all('text="登录"')
            if login_buttons:
                print("❌ 需要登录")
                print("📱 请在浏览器中完成登录...")
                print("   - 可以使用手机扫码登录")
                print("   - 或者输入账号密码登录")
                print("✅ 登录完成后按回车继续...")
                input()
                
                # 再次检查
                await self.page.reload()
                await asyncio.sleep(2)
                login_buttons = await self.page.query_selector_all('text="登录"')
                if login_buttons:
                    print("❌ 仍未登录")
                    return False
            
            print("✅ 登录状态正常")
            return True
            
        except Exception as e:
            print(f"❌ 登录检查失败: {e}")
            return False
    
    async def get_target_notes(self):
        """获取目标笔记列表"""
        print("📋 获取目标笔记...")
        
        # 剩余需要评论的笔记
        target_notes = [
            {
                "url": "https://www.xiaohongshu.com/search_result/6882e99f00000000220302c0",
                "title": "花了35万全屋定制，避雷图森高端定制"
            },
            {
                "url": "https://www.xiaohongshu.com/search_result/687c8317000000001d00cf98",
                "title": "全屋定制避坑指南"
            },
            {
                "url": "https://www.xiaohongshu.com/search_result/6881f7bb0000000017030ae3",
                "title": "全屋定制经验分享"
            },
            {
                "url": "https://www.xiaohongshu.com/search_result/68771bde000000001203fa26",
                "title": "定制家具选择攻略"
            },
            {
                "url": "https://www.xiaohongshu.com/search_result/6881eb170000000011001d55",
                "title": "全屋定制价格分析"
            },
            {
                "url": "https://www.xiaohongshu.com/search_result/68823e87000000002203fd66",
                "title": "定制衣柜经验"
            },
            {
                "url": "https://www.xiaohongshu.com/search_result/6880d018000000001202dd79",
                "title": "全屋定制材料选择"
            }
        ]
        
        print(f"✅ 准备处理 {len(target_notes)} 个目标笔记")
        return target_notes
    
    async def find_say_something_input(self, comment):
        """专门查找"说点什么"评论输入框"""
        print('🔍 专门查找"说点什么"评论框...')
        
        try:
            result = await self.page.evaluate(f"""
                (comment) => {{
                    console.log('开始查找"说点什么"评论输入框...');
                    
                    // 查找所有包含"说点什么"的元素
                    const sayElements = [];
                    const allElements = document.querySelectorAll('*');
                    
                    for (const el of allElements) {{
                        const text = el.textContent || el.placeholder || el.getAttribute('placeholder') || '';
                        if (text.includes('说点什么')) {{
                            sayElements.push(el);
                        }}
                    }}
                    
                    console.log('找到"说点什么"元素数量:', sayElements.length);
                    
                    for (const sayEl of sayElements) {{
                        console.log('处理"说点什么"元素:', sayEl.tagName, sayEl.className);
                        
                        let targetInput = null;
                        
                        // 检查元素本身是否是输入框
                        if (sayEl.tagName === 'TEXTAREA' || 
                            sayEl.tagName === 'INPUT' || 
                            sayEl.contentEditable === 'true') {{
                            targetInput = sayEl;
                        }}
                        
                        // 在元素内部查找输入框
                        if (!targetInput) {{
                            const inputs = sayEl.querySelectorAll('textarea, input, div[contenteditable="true"]');
                            if (inputs.length > 0) {{
                                targetInput = inputs[0];
                            }}
                        }}
                        
                        // 在父元素中查找输入框
                        if (!targetInput && sayEl.parentElement) {{
                            const parentInputs = sayEl.parentElement.querySelectorAll('textarea, input, div[contenteditable="true"]');
                            if (parentInputs.length > 0) {{
                                targetInput = parentInputs[0];
                            }}
                        }}
                        
                        // 在兄弟元素中查找输入框
                        if (!targetInput && sayEl.parentElement) {{
                            const siblings = sayEl.parentElement.children;
                            for (const sibling of siblings) {{
                                if (sibling.tagName === 'TEXTAREA' || 
                                    sibling.tagName === 'INPUT' || 
                                    sibling.contentEditable === 'true') {{
                                    targetInput = sibling;
                                    break;
                                }}
                                const siblingInputs = sibling.querySelectorAll('textarea, input, div[contenteditable="true"]');
                                if (siblingInputs.length > 0) {{
                                    targetInput = siblingInputs[0];
                                    break;
                                }}
                            }}
                        }}
                        
                        if (targetInput) {{
                            const rect = targetInput.getBoundingClientRect();
                            console.log('找到目标输入框:', targetInput.tagName, targetInput.className);
                            console.log('位置信息:', `x:${{rect.left}}, y:${{rect.top}}, w:${{rect.width}}, h:${{rect.height}}`);
                            
                            if (rect.width > 0 && rect.height > 0) {{
                                try {{
                                    // 滚动到输入框
                                    targetInput.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                                    
                                    // 等待滚动完成
                                    await new Promise(resolve => setTimeout(resolve, 1500));
                                    
                                    // 点击激活输入框
                                    targetInput.click();
                                    targetInput.focus();
                                    
                                    await new Promise(resolve => setTimeout(resolve, 800));
                                    
                                    // 清空现有内容
                                    if (targetInput.tagName === 'DIV') {{
                                        targetInput.innerHTML = '';
                                        targetInput.textContent = '';
                                    }} else {{
                                        targetInput.value = '';
                                    }}
                                    
                                    // 输入评论内容
                                    if (targetInput.tagName === 'DIV') {{
                                        targetInput.innerHTML = comment;
                                        targetInput.textContent = comment;
                                    }} else {{
                                        targetInput.value = comment;
                                    }}
                                    
                                    // 触发输入事件
                                    const events = ['input', 'change', 'keyup', 'focus'];
                                    for (const eventType of events) {{
                                        const event = new Event(eventType, {{ bubbles: true, cancelable: true }});
                                        targetInput.dispatchEvent(event);
                                    }}
                                    
                                    console.log('输入完成，查找发送按钮...');
                                    
                                    await new Promise(resolve => setTimeout(resolve, 1000));
                                    
                                    // 查找发送按钮
                                    let sendButton = null;
                                    
                                    // 在同一容器中查找
                                    const container = targetInput.closest('div, form, section');
                                    if (container) {{
                                        const buttons = container.querySelectorAll('button');
                                        for (const btn of buttons) {{
                                            const btnText = btn.textContent || btn.innerText || '';
                                            if (btnText.includes('发送') || btnText.includes('发布') || btnText.includes('提交')) {{
                                                sendButton = btn;
                                                break;
                                            }}
                                        }}
                                    }}
                                    
                                    // 在整个页面查找发送按钮
                                    if (!sendButton) {{
                                        const allButtons = document.querySelectorAll('button');
                                        for (const btn of allButtons) {{
                                            const btnText = btn.textContent || btn.innerText || '';
                                            if (btnText.includes('发送') || btnText.includes('发布')) {{
                                                const btnRect = btn.getBoundingClientRect();
                                                if (btnRect.width > 0 && btnRect.height > 0) {{
                                                    sendButton = btn;
                                                    break;
                                                }}
                                            }}
                                        }}
                                    }}
                                    
                                    if (sendButton) {{
                                        console.log('找到发送按钮，点击发送');
                                        sendButton.click();
                                        return {{ success: true, method: 'button_click', element: targetInput.tagName }};
                                    }} else {{
                                        console.log('未找到发送按钮，尝试回车键');
                                        const enterEvent = new KeyboardEvent('keydown', {{
                                            key: 'Enter',
                                            code: 'Enter',
                                            keyCode: 13,
                                            bubbles: true,
                                            cancelable: true
                                        }});
                                        targetInput.dispatchEvent(enterEvent);
                                        return {{ success: true, method: 'enter_key', element: targetInput.tagName }};
                                    }}
                                    
                                }} catch (e) {{
                                    console.error('操作输入框失败:', e);
                                    continue;
                                }}
                            }}
                        }}
                    }}
                    
                    return {{ success: false, reason: 'no_say_something_found' }};
                }}
            """, comment)
            
            return result
            
        except Exception as e:
            print(f"❌ JavaScript执行失败: {e}")
            return {"success": False, "reason": "js_error"}
    
    async def comment_with_retry(self, url, comment, title, max_retries=3):
        """带重试的评论方法"""
        print(f"💬 评论: {title}")
        
        for attempt in range(max_retries):
            try:
                # 确保浏览器准备就绪
                await self.ensure_browser_ready()
                
                print(f"🔗 访问页面 (尝试 {attempt + 1}/{max_retries})")
                await self.page.goto(url, timeout=60000)
                await asyncio.sleep(8)
                
                # 检查页面有效性
                page_content = await self.page.content()
                if any(error in page_content for error in ["当前笔记暂时无法浏览", "内容不存在", "页面不存在"]):
                    print("⚠️ 页面无效，跳过")
                    return False
                
                # 滚动页面，确保评论区域加载
                print("📜 滚动页面加载评论区...")
                await self.page.evaluate("""
                    () => {
                        // 分步滚动
                        window.scrollTo(0, document.body.scrollHeight / 3);
                        setTimeout(() => {
                            window.scrollTo(0, document.body.scrollHeight * 2 / 3);
                            setTimeout(() => {
                                window.scrollTo(0, document.body.scrollHeight);
                            }, 1000);
                        }, 1000);
                    }
                """)
                await asyncio.sleep(6)
                
                # 查找并操作"说点什么"输入框
                result = await self.find_say_something_input(comment)
                
                if result.get('success'):
                    print(f"✅ 评论成功! (方法: {result.get('method')}, 元素: {result.get('element')})")
                    await asyncio.sleep(3)  # 等待评论提交完成
                    return True
                else:
                    print(f"❌ 第{attempt + 1}次尝试失败: {result.get('reason')}")
                    if attempt < max_retries - 1:
                        print(f"⏳ 等待 {5 * (attempt + 1)} 秒后重试...")
                        await asyncio.sleep(5 * (attempt + 1))
                
            except Exception as e:
                print(f"❌ 第{attempt + 1}次尝试出错: {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ 等待 {10 * (attempt + 1)} 秒后重试...")
                    await asyncio.sleep(10 * (attempt + 1))
        
        # 所有尝试都失败了，提供手动选项
        print("🔧 自动评论失败，提供手动辅助...")
        print(f"💬 请手动在浏览器中为这个笔记添加评论: {comment}")
        print("📍 请在页面中找到包含'说点什么'的评论输入框")
        print("✅ 完成后按回车继续...")
        input()
        return True  # 假设手动完成了
    
    async def run_stable_task(self):
        """运行稳定的评论任务"""
        print("🎯 启动稳定的小红书评论机器人")
        print("=" * 60)
        
        try:
            # 初始化浏览器
            await self.init_browser()
            
            # 检查登录状态
            if not await self.quick_login_check():
                print("❌ 登录失败，程序退出")
                return
            
            # 获取目标笔记
            notes = await self.get_target_notes()
            
            print(f"📝 开始处理 {len(notes)} 个笔记...")
            print("🎯 专门查找'说点什么'评论输入框")
            
            # 逐个评论
            success_count = 0
            for i, note in enumerate(notes, 1):
                print(f"\n📌 [{i}/{len(notes)}] {note['title']}")
                
                # 随机等待
                wait_time = random.uniform(15, 25)
                print(f"⏳ 等待 {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                
                # 评论
                if await self.comment_with_retry(note['url'], "我自荐，可以看看我的主页", note['title']):
                    success_count += 1
                    print(f"✅ 成功 [{success_count}/{i}]")
                else:
                    print(f"❌ 失败 [{success_count}/{i}]")
                
                # 每2个笔记休息
                if i % 2 == 0 and i < len(notes):
                    rest_time = random.uniform(60, 90)
                    print(f"😴 长休息 {rest_time:.1f}s...")
                    await asyncio.sleep(rest_time)
            
            print("\n" + "=" * 60)
            print(f"🎉 稳定任务完成！")
            print(f"📊 最终成功率: {success_count}/{len(notes)} ({success_count/len(notes)*100:.1f}%)")
            
        except Exception as e:
            print(f"❌ 任务执行出错: {e}")
        finally:
            print("🔚 浏览器保持打开状态，可以手动检查结果")

async def main():
    bot = StableCommentBot()
    await bot.run_stable_task()

if __name__ == "__main__":
    asyncio.run(main())