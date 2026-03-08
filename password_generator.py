import queue


def get_custom_keywords():
    """获取用户自定义的关键字"""
    print("\n" + "="*80)
    print("🔑 自定义密码关键字配置")
    print("="*80)
    print("\n请输入密码关键字，输入 'exit' 结束输入")
    print("例如: zhang (回车) san (回车) exit (回车)")
    
    keywords = []
    print("\n开始输入关键字:")
    
    while True:
        user_input = input("  > ").strip()
        
        if user_input.lower() == 'exit':
            if len(keywords) == 0:
                print("❌ 必须至少输入一个关键字")
                continue
            break
        
        if user_input:
            # 保持原始输入
            keywords.append(user_input)
            print(f"  ✅ 添加: {user_input}")
            
            # 首字母大写
            capitalized = user_input.capitalize()
            if capitalized != user_input:
                keywords.append(capitalized)
                print(f"  ✅ 添加: {capitalized}")
            
            # 全大写
            uppercase = user_input.upper()
            if uppercase != user_input and uppercase != capitalized:
                keywords.append(uppercase)
                print(f"  ✅ 添加: {uppercase}")
            
            # 全小写
            lowercase = user_input.lower()
            if lowercase != user_input and lowercase != capitalized and lowercase != uppercase:
                keywords.append(lowercase)
                print(f"  ✅ 添加: {lowercase}")
    
    print(f"\n✅ 已添加 {len(keywords)} 个关键字:")
    for i, kw in enumerate(keywords, 1):
        print(f"   {i}. {kw}")
    
    confirm = input("\n确认使用这些关键字？(y/n): ").lower()
    if confirm == 'y':
        return keywords
    else:
        print("请重新输入...")
        return get_custom_keywords()


def get_custom_dates():
    """获取用户自定义的特殊日期"""
    print("\n" + "="*80)
    print("📅 自定义特殊日期配置")
    print("="*80)
    print("\n请输入特殊日期（4位数字），输入 'exit' 结束输入")
    print("例如: 0406 (回车) 1229 (回车) exit (回车)")
    
    dates = []
    print("\n开始输入日期:")
    
    while True:
        user_input = input("  > ").strip()
        
        if user_input.lower() == 'exit':
            if len(dates) == 0:
                print("❌ 必须至少输入一个日期")
                continue
            break
        
        if user_input and len(user_input) == 4 and user_input.isdigit():
            dates.append(user_input)
            print(f"  ✅ 添加: {user_input}")
        elif user_input:
            print("  ⚠ 请输入4位数字的日期（如 0406）")
    
    print(f"\n✅ 已添加 {len(dates)} 个特殊日期:")
    for i, date in enumerate(dates, 1):
        print(f"   {i}. {date}")
    
    confirm = input("\n确认使用这些日期？(y/n): ").lower()
    if confirm == 'y':
        return dates
    else:
        print("请重新输入...")
        return get_custom_dates()

def get_custom_years():
    """获取用户自定义的年份范围"""
    print("\n" + "="*80)
    print("📅 自定义年份范围配置")
    print("="*80)
    print("\n请输入年份范围的开始年份和结束年份")
    print("例如: 2000 2025")
    
    while True:
        user_input = input("\n请输入年份范围（用空格分隔）: ").strip()
        parts = user_input.split()
        
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            start_year = int(parts[0])
            end_year = int(parts[1])
            
            if start_year <= end_year and start_year >= 1900 and end_year <= 2100:
                print(f"\n✅ 年份范围设置为: {start_year} - {end_year}")
                return start_year, end_year
            else:
                print("❌ 年份范围无效，请确保开始年份小于等于结束年份，且在 1900-2100 之间")
        else:
            print("❌ 输入格式错误，请输入两个数字年份，用空格分隔")


def generate_passwords(custom_keywords, custom_dates, start_year, end_year):
    """生成密码组合"""
    str1 = custom_keywords
    
    # 年份和两位数字
    str2 = [str(year) for year in range(start_year, end_year + 1)]
    str2.extend([f"{num:02d}" for num in range(0, 25)])
    
    # 特殊日期
    str3 = custom_dates
    
    # 特殊符号
    special_chars = ["", "!", "@", "#", "$", "%", "^", "&"]
    
    # 生成密码队列
    password_queue = queue.Queue()
    generated_count = 0
    
    print("\n🔑 生成密码组合...")
    
    # 组合1: 关键字 + 特殊符号 + 年份
    print("  生成组合: 关键字 + 特殊符号 + 年份")
    for p1 in str1:
        for char in special_chars:
            for p2 in str2:
                password_queue.put(p1 + char + p2)
                generated_count += 1
    
    # 组合2: 关键字 + 特殊符号 + 日期
    print("  生成组合: 关键字 + 特殊符号 + 日期")
    for p1 in str1:
        for char in special_chars:
            for p3 in str3:
                password_queue.put(p1 + char + p3)
                generated_count += 1
    
    # 组合3: 关键字 + 特殊符号 + 年份 + 日期
    print("  生成组合: 关键字 + 特殊符号 + 年份 + 日期")
    for p1 in str1:
        for char in special_chars:
            for p2 in str2:
                for p3 in str3:
                    password_queue.put(p1 + char + p2 + p3)
                    generated_count += 1
    
    # 组合4: 关键字 + 年份 + 日期
    print("  生成组合: 关键字 + 年份 + 日期")
    for p1 in str1:
        for p2 in str2:
            for p3 in str3:
                password_queue.put(p1 + p2 + p3)
                generated_count += 1
    
    # 组合5: 关键字 + 年份
    print("  生成组合: 关键字 + 年份")
    for p1 in str1:
        for p2 in str2:
            password_queue.put(p1 + p2)
            generated_count += 1
    
    # 组合6: 关键字 + 日期
    print("  生成组合: 关键字 + 日期")
    for p1 in str1:
        for p3 in str3:
            password_queue.put(p1 + p3)
            generated_count += 1
    
    # 组合7: 年份 + 日期
    print("  生成组合: 年份 + 日期")
    for p2 in str2:
        for p3 in str3:
            password_queue.put(p2 + p3)
            generated_count += 1
    
    # 组合8: 日期
    print("  生成组合: 日期")
    for p3 in str3:
        password_queue.put(p3)
        generated_count += 1
    
    # 组合9: 关键字 + 年份 + 日期 + 特殊符号
    print("  生成组合: 关键字 + 年份 + 日期 + 特殊符号")
    for p1 in str1:
        for p2 in str2:
            for p3 in str3:
                for char in special_chars:
                    if char:
                        password_queue.put(p1 + p2 + p3 + char)
                        generated_count += 1
    
    # 组合10: 关键字 + 年份 + 特殊符号
    print("  生成组合: 关键字 + 年份 + 特殊符号")
    for p1 in str1:
        for p2 in str2:
            for char in special_chars:
                if char:
                    password_queue.put(p1 + p2 + char)
                    generated_count += 1
    
    # 组合11: 关键字 + 日期 + 特殊符号
    print("  生成组合: 关键字 + 日期 + 特殊符号")
    for p1 in str1:
        for p3 in str3:
            for char in special_chars:
                if char:
                    password_queue.put(p1 + p3 + char)
                    generated_count += 1
    
    # 组合12: 年份 + 日期 + 特殊符号
    print("  生成组合: 年份 + 日期 + 特殊符号")
    for p2 in str2:
        for p3 in str3:
            for char in special_chars:
                if char:
                    password_queue.put(p2 + p3 + char)
                    generated_count += 1
    
    total_passwords = password_queue.qsize()
    
    print(f"\n✅ 密码生成完成:")
    print(f"   总密码数: {total_passwords:,}")
    print(f"   组合方式: {len(str1)} × {len(str2)} × {len(str3)} + {len(str1)} × {len(str3)}")
    
    # 显示示例密码
    print("\n📋 密码示例:")
    samples = []
    temp_queue = queue.Queue()
    
    for _ in range(min(5, total_passwords)):
        pwd = password_queue.get()
        samples.append(pwd)
        temp_queue.put(pwd)
    
    # 还原队列
    while not temp_queue.empty():
        password_queue.put(temp_queue.get())
    
    for i, sample in enumerate(samples, 1):
        print(f"   {i}. {sample}")
    
    return password_queue, total_passwords
