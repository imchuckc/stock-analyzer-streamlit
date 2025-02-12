def analyze_stock(df):
    """Analyze stock data and return signals"""
    signals = []
    latest = df.iloc[-1]
    
    # Price trend analysis
    if latest['Close'] > latest['MA20']:
        signals.append(("Bullish", "Price above MA20"))
    else:
        signals.append(("Bearish", "Price below MA20"))
        
    # MA Cross analysis
    if latest['MA5'] > latest['MA20']:
        signals.append(("Bullish", "MA5 above MA20"))
    else:
        signals.append(("Bearish", "MA5 below MA20"))
        
    # Bollinger Bands analysis
    if latest['Close'] > latest['BB_UPPER']:
        signals.append(("Overbought", "Price above upper BB"))
    elif latest['Close'] < latest['BB_LOWER']:
        signals.append(("Oversold", "Price below lower BB"))
        
    return signals

def analyze_stock_commentary(df):
    """Generate professional stock analysis commentary"""
    # 获取最新数据和前一日数据
    latest = df.iloc[-1]
    prev_day = df.iloc[-2]
    commentary = []
    
    # 计算5日平均成交量（提前计算，确保可用）
    df['avg_volume'] = df['Volume'].rolling(window=5).mean()
    latest_avg_volume = df['avg_volume'].iloc[-1]  # 获取最新的平均成交量
    
    # 技术指标分析
    commentary.append("技术指标分析：")
    
    # RSI分析
    commentary.append("\nRSI指标:")
    if latest['RSI'] > 70:
        commentary.append(f"  - RSI处于超买区间 ({latest['RSI']:.1f})")
        commentary.append("  - 警惕可能出现回调风险")
    elif latest['RSI'] < 30:
        commentary.append(f"  - RSI处于超卖区间 ({latest['RSI']:.1f})")
        commentary.append("  - 关注可能出现的反弹机会")
    else:
        commentary.append(f"  - RSI处于中性区间 ({latest['RSI']:.1f})")
    
    # BIAS分析
    commentary.append("\n乖离率分析:")
    # 5日乖离率分析
    bias5_str = f"5日乖离率: <span class='number-highlight'>{latest['BIAS5']:.2f}%</span>"
    if latest['BIAS5'] > 6:
        commentary.append(f"  - {bias5_str} - 短期严重偏离，有超买风险")
    elif latest['BIAS5'] < -6:
        commentary.append(f"  - {bias5_str} - 短期严重偏离，有超卖机会")
    else:
        commentary.append(f"  - {bias5_str} - 短期偏离度适中")
        
    # 10日乖离率分析
    bias10_str = f"10日乖离率: <span class='number-highlight'>{latest['BIAS10']:.2f}%</span>"
    if latest['BIAS10'] > 8:
        commentary.append(f"  - {bias10_str} - 中期偏离过大，注意回归风险")
    elif latest['BIAS10'] < -8:
        commentary.append(f"  - {bias10_str} - 中期偏离过大，可能存在修复机会")
    else:
        commentary.append(f"  - {bias10_str} - 中期偏离度合理")
        
    # 20日乖离率分析
    bias20_str = f"20日乖离率: <span class='number-highlight'>{latest['BIAS20']:.2f}%</span>"
    if latest['BIAS20'] > 10:
        commentary.append(f"  - {bias20_str} - 长期严重偏离，建议保持谨慎")
    elif latest['BIAS20'] < -10:
        commentary.append(f"  - {bias20_str} - 长期严重偏离，可能存在价值")
    else:
        commentary.append(f"  - {bias20_str} - 长期偏离度正常")
    
    # 综合乖离率分析
    if abs(latest['BIAS5']) > 6 and abs(latest['BIAS10']) > 8 and abs(latest['BIAS20']) > 10:
        if latest['BIAS5'] > 0:
            commentary.append("  - 各周期乖离率均处于高位，股价可能存在较大回调压力")
        else:
            commentary.append("  - 各周期乖离率均处于低位，股价可能存在较大反弹空间")
    elif abs(latest['BIAS5']) < 6 and abs(latest['BIAS10']) < 8 and abs(latest['BIAS20']) < 10:
        commentary.append("  - 各周期乖离率均处于合理区间，股价运行平稳")
    
    # MACD分析
    commentary.append("\nMACD指标:")
    if latest['MACD'] > latest['Signal']:
        if latest['MACD_Hist'] > prev_day['MACD_Hist']:
            commentary.append("  - MACD金叉后柱状量持续放大")
            commentary.append("  - 上涨动能较强")
        else:
            commentary.append("  - MACD处于多头格局")
            commentary.append("  - 但力度有所减弱")
    else:
        if latest['MACD_Hist'] < prev_day['MACD_Hist']:
            commentary.append("  - MACD死叉后柱状量继续减小")
            commentary.append("  - 下跌趋势未改")
        else:
            commentary.append("  - MACD处于空头格局")
            commentary.append("  - 但跌势可能趋缓")
    
    # 布林带分析
    commentary.append("\n布林带分析:")
    if latest['Close'] > latest['BB_UPPER']:
        commentary.append("  - 股价突破布林带上轨")
        commentary.append("  - 短期超买，注意回调风险")
    elif latest['Close'] < latest['BB_LOWER']:
        commentary.append("  - 股价跌破布林带下轨")
        commentary.append("  - 短期超卖，关注反弹机会")
    else:
        bb_middle = (latest['BB_UPPER'] + latest['BB_LOWER']) / 2
        if latest['Close'] > bb_middle:
            commentary.append("  - 股价运行于布林带上方")
            commentary.append("  - 短期走势偏强")
        else:
            commentary.append("  - 股价运行于布林带下方")
            commentary.append("  - 短期走势偏弱")
    
    # 量价分析
    commentary.append("\n量价分析：")
    
    # 计算成交量比率
    volume_ratio = latest['Volume'] / latest_avg_volume
    price_change = (latest['Close'] - prev_day['Close']) / prev_day['Close']
    
    # 成交量状态判断
    if volume_ratio > 4.0:  # 特别巨量
        commentary.append(f"• 成交量较前期巨量放大 ({volume_ratio:.1f}倍)")
        if price_change > 0:
            commentary.append("• 放量上涨，买盘积极，上涨有效")
        else:
            commentary.append("• 巨量下跌，抛压沉重，需谨慎对待")
    elif volume_ratio > 2.0:  # 明显放量
        commentary.append(f"• 成交量较前期明显放大 ({volume_ratio:.1f}倍)")
        if price_change > 0:
            commentary.append("• 量价配合良好，上涨有支撑")
        else:
            commentary.append("• 放量下跌，卖压较重")
    elif volume_ratio > 1.2:  # 小幅放量
        commentary.append(f"• 成交量较前期小幅放大 ({volume_ratio:.1f}倍)")
        if price_change > 0:
            commentary.append("• 小幅放量上涨，走势偏强")
        else:
            commentary.append("• 小幅放量下跌，需密切关注")
    elif volume_ratio < 0.8:  # 量能萎缩
        commentary.append(f"• 成交量较前期萎缩 ({volume_ratio:.1f}倍)")
        if price_change > 0:
            commentary.append("• 缩量上涨，上涨动能不足")
        else:
            commentary.append("• 缩量下跌，跌势可能趋缓")
    else:  # 量能平稳
        commentary.append(f"• 成交量基本持平 ({volume_ratio:.1f}倍)")
        commentary.append("• 市场交投一般，观望情绪较浓")
    
    # 均线系统分析
    commentary.append("\n均线系统分析：")
    
    # 短线分析（5日、10日均线）
    commentary.append("\n• 短线分析:")
    if latest['MA5'] > latest['MA10']:
        commentary.append("  - MA5上穿MA10，短线走势转强")
        if latest['Close'] > latest['MA5']:
            commentary.append("  - 价格站上短期均线，短线可偏乐观")
    else:
        commentary.append("  - MA5下穿MA10，短线走势转弱")
        if latest['Close'] < latest['MA5']:
            commentary.append("  - 价格跌破短期均线，短线需谨慎")
    
    # 中线分析（20日、30日均线）
    commentary.append("\n• 中线分析:")
    if latest['MA20'] > latest['MA30']:
        commentary.append("  - MA20上穿MA30，中期趋势向好")
        if latest['Close'] > latest['MA20']:
            commentary.append("  - 价格站上中期均线，中线可看高一线")
    else:
        commentary.append("  - MA20下穿MA30，中期趋势转弱")
        if latest['Close'] < latest['MA20']:
            commentary.append("  - 价格跌破中期均线，中线宜观望")
    
    return commentary

def analyze_support_resistance(df):
    """分析支撑压力位并生成HTML格式的分析报告"""
    if 'support_levels' not in df.columns or 'resistance_levels' not in df.columns:
        return "暂无支撑压力位数据"
        
    current_price = df['Close'].iloc[-1]
    support_levels = df['support_levels'].iloc[0]
    resistance_levels = df['resistance_levels'].iloc[0]
    support_strengths = df['support_strengths'].iloc[0] if 'support_strengths' in df.columns else None
    resistance_strengths = df['resistance_strengths'].iloc[0] if 'resistance_strengths' in df.columns else None
    
    # 如果类型信息不存在，根据位置分配默认的算法类型
    if 'support_types' in df.columns:
        support_types = df['support_types'].iloc[0]
    else:
        support_types = ['1', '2', '3'] * (len(support_levels) // 3 + 1)  # 循环使用三种算法
        support_types = support_types[:len(support_levels)]  # 截取需要的长度
    
    if 'resistance_types' in df.columns:
        resistance_types = df['resistance_types'].iloc[0]
    else:
        resistance_types = ['1', '2', '3'] * (len(resistance_levels) // 3 + 1)  # 循环使用三种算法
        resistance_types = resistance_types[:len(resistance_levels)]  # 截取需要的长度
    
    analysis = []
    
    # 添加当前价格信息
    analysis.append(f"• 当前价格: <span class='price-current'>{current_price:.2f}</span>")
    
    # 分析所有支撑位
    if support_levels:
        supports_below = [(s, i) for i, s in enumerate(support_levels) if s < current_price]
        if supports_below:
            analysis.append("\n• 支撑位分析:")
            # 按价格从高到低排序
            supports_below.sort(reverse=True)
            for support, idx in supports_below:
                support_distance = (current_price - support) / current_price * 100
                
                # 获取算法类型描述
                type_info = support_types[idx]
                type_desc = {
                    '1': '枢轴点位法',
                    '2': '成交量分布法',
                    '3': '分形理论法'
                }.get(str(type_info), '未知算法')
                
                strength_info = ""
                if support_strengths:
                    strength = support_strengths[idx]
                    strength_desc = "极强" if strength >= 80 else \
                                  "强" if strength >= 60 else \
                                  "中等" if strength >= 40 else \
                                  "弱" if strength >= 20 else "极弱"
                    strength_info = f"强度: <span style='color: green;'>{strength:.0f}</span>分({strength_desc})"
                
                analysis.append(f"  - <span style='color: green;'>{support:.2f}</span> | {type_desc} | 距离: <span style='color: green;'>{support_distance:.1f}%</span> | {strength_info}")
    
    # 分析所有压力位
    if resistance_levels:
        resistances_above = [(r, i) for i, r in enumerate(resistance_levels) if r > current_price]
        if resistances_above:
            analysis.append("\n• 压力位分析:")
            # 按价格从低到高排序
            resistances_above.sort()
            for resistance, idx in resistances_above:
                resistance_distance = (resistance - current_price) / current_price * 100
                
                # 获取算法类型描述
                type_info = resistance_types[idx]
                type_desc = {
                    '1': '枢轴点位法',
                    '2': '成交量分布法',
                    '3': '分形理论法'
                }.get(str(type_info), '未知算法')
                
                strength_info = ""
                if resistance_strengths:
                    strength = resistance_strengths[idx]
                    strength_desc = "极强" if strength >= 80 else \
                                  "强" if strength >= 60 else \
                                  "中等" if strength >= 40 else \
                                  "弱" if strength >= 20 else "极弱"
                    strength_info = f"强度: <span class='number-highlight'>{strength:.0f}</span>分({strength_desc})"
                
                analysis.append(f"  - <span class='price-resistance'>{resistance:.2f}</span> | {type_desc} | 距离: <span class='number-highlight'>{resistance_distance:.1f}%</span> | {strength_info}")
    
    # 添加位置判断
    if support_levels and resistance_levels:
        total_range = max(resistance_levels) - min(support_levels)
        current_position = (current_price - min(support_levels)) / total_range * 100
        analysis.append(f"\n• 价格位置: 处于支撑压力区间<span class='number-highlight'>{current_position:.1f}%</span>处")
        
        # 添加趋势建议
        if current_position > 80:
            analysis.append("• 建议: 位于高位，注意回调风险")
        elif current_position < 20:
            analysis.append("• 建议: 位于低位，关注反弹机会")
        else:
            analysis.append("• 建议: 位于中位，可高抛低吸")
    
    return "<br>".join(analysis) 

def analyze_volume_price(df):
    """分析量价关系"""
    # 计算最近5日平均成交量
    df['avg_volume'] = df['volume'].rolling(window=5).mean()
    
    # 获取最新数据
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 计算成交量相对于5日均量的变化
    volume_ratio = latest['volume'] / latest['avg_volume']
    
    # 计算价格变化
    price_change = (latest['close'] - prev['close']) / prev['close']
    
    # 量价分析结论
    analysis = []
    
    # 成交量分析
    if volume_ratio > 1.5:
        volume_status = "显著放量"
    elif volume_ratio > 1.2:
        volume_status = "小幅放量"
    elif volume_ratio < 0.5:
        volume_status = "量能萎缩"
    else:
        volume_status = "量能平稳"
        
    analysis.append(f"成交量状况：{volume_status}（当前成交量为5日均量的{volume_ratio:.2f}倍）")
    
    # 量价配合分析
    if volume_ratio > 1.2:  # 放量
        if price_change > 0:
            analysis.append("量价配合良好，上涨有支撑")
        else:
            analysis.append("放量下跌，可能存在较大抛压")
    elif volume_ratio < 0.8:  # 缩量
        if price_change > 0:
            analysis.append("缩量上涨，上涨动能不足")
        else:
            analysis.append("缩量下跌，跌势可能趋缓")
    else:
        analysis.append("量价变化平稳，市场观望情绪较浓")
    
    return "\n".join(analysis) 