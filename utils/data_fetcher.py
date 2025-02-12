import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import time
import numpy as np

# Tab1: 市场概览数据
@st.cache_data(ttl=14400)  # 4小时缓存
def get_market_overview():
    """Tab1: 获取市场概览数据"""
    try:
        # 获取指数数据
        indices = {
            '上证指数': 'sh000001',
            '深证成指': 'sz399001',
            '创业板指': 'sz399006'
        }
        
        market_data = {}
        df = ak.stock_zh_index_spot()  # 只调用一次API
        for name, code in indices.items():
            market_data[name] = df[df['代码'] == code].iloc[0].to_dict()
        
        # 获取行业板块数据
        try:
            sector_df = ak.stock_board_industry_name_em()
        except Exception as e:
            print(f"Error getting sector data: {e}")
            sector_df = None
            
        # 获取概念板块数据
        try:
            concept_df = ak.stock_board_concept_name_em()
        except Exception as e:
            print(f"Error getting concept data: {e}")
            concept_df = None
            
        return market_data, sector_df, concept_df
    except Exception as e:
        print(f"Error getting market overview: {e}")
        return {}, None, None

# Tab2: 热门板块相关数据
@st.cache_data(ttl=43200)  # 12小时缓存
def get_hot_sectors_data():
    """Tab2: 获取热门板块数据，仅在Tab2中使用"""
    try:
        df = ak.stock_board_industry_hist_em()
        df['日期'] = pd.to_datetime(df['日期'])
        return df
    except Exception as e:
        print(f"Error getting hot sectors data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=43200)
def get_top_sectors_history(days=10, top_n=10):
    """Tab2: 处理热门板块数据"""
    try:
        df = get_hot_sectors_data()
        if df.empty:
            return pd.DataFrame()
            
        df = df.sort_values('日期', ascending=False)
        
        # 获取最近days天的数据
        latest_date = df['日期'].max()
        start_date = latest_date - timedelta(days=days)
        df = df[df['日期'] >= start_date]
        
        # 按日期分组，每天选出涨幅前10的板块
        daily_top_sectors = []
        for date, day_data in df.groupby('日期'):
            top_of_day = day_data.nlargest(10, '涨跌幅')['板块名称'].tolist()
            daily_top_sectors.extend([(sector, date) for sector in top_of_day])
        
        # 统计上榜次数
        top_sectors_df = pd.DataFrame(daily_top_sectors, columns=['板块名称', '日期'])
        sector_counts = top_sectors_df['板块名称'].value_counts()
        
        # 获取上榜次数最多的前N个板块
        top_sectors = sector_counts.nlargest(top_n)
        
        # 计算排名
        sector_ranks = sector_counts.rank(method='min', ascending=False)
        
        # 获取这些板块的所有历史数据
        result_df = df[df['板块名称'].isin(top_sectors.index)].copy()
        
        # 添加统计信息
        result_df['上榜次数'] = result_df['板块名称'].map(sector_counts)
        result_df['上榜排名'] = result_df['板块名称'].map(sector_ranks)
        result_df['平均涨跌幅'] = result_df.groupby('板块名称')['涨跌幅'].transform('mean')
        
        return result_df.sort_values(['上榜次数', '平均涨跌幅'], ascending=[False, False])
    except Exception as e:
        print(f"Error processing top sectors: {e}")
        return pd.DataFrame()

# Tab3: 板块个股分析相关数据
@st.cache_data(ttl=43200)
def get_all_sectors():
    """Tab3: 获取所有板块列表，仅在Tab3中使用"""
    try:
        df = ak.stock_board_industry_name_em()
        return df
    except Exception as e:
        print(f"Error getting all sectors: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=43200)
def get_sector_list():
    """获取所有板块列表"""
    try:
        df = ak.stock_board_industry_name_em()
        return df['板块名称'].tolist()
    except Exception as e:
        print(f"Error getting sector list: {e}")
        return []

@st.cache_data(ttl=43200)
def get_sector_stocks(sector_name):
    """获取板块成分股"""
    try:
        df = ak.stock_board_industry_cons_em(symbol=sector_name)
        return df
    except Exception as e:
        print(f"Error getting sector stocks: {e}")
        return None

# Tab4: 个股分析工具相关数据
@st.cache_data(ttl=86400, show_spinner=False)  # 24小时缓存
def get_stock_list():
    """获取股票列表"""
    try:
        df = ak.stock_info_a_code_name()
        # 创建一个字典，键为 "股票名称 (股票代码)"，值为股票代码
        stock_dict = {f"{row['name']} ({row['code']})": row['code'] 
                     for _, row in df.iterrows()}
        return stock_dict
    except Exception as e:
        print(f"Error getting stock list: {e}")
        return {}

def calculate_support_resistance(df, window=20, price_threshold=0.02, touch_count=2):
    """计算支撑和压力位，使用多种专业技术分析方法，并计算强度分数
    
    Methods:
    1. Pivot Points (枢轴点位)
    2. Volume Profile (成交量分布)
    3. Fractal Levels (分形水平)
    
    Strength Score Factors:
    1. 价格触及次数 (40%)
    2. 成交量支持度 (30%)
    3. 近期有效性 (20%)
    4. 反弹/回落幅度 (10%)
    
    Args:
        df: DataFrame with OHLC data
        window: 寻找分形的窗口大小
        price_threshold: 价格聚类阈值
        touch_count: 确认支撑/压力位需要的最小触及次数
    
    Returns:
        support_levels: List of (price, score) tuples for support levels
        resistance_levels: List of (price, score) tuples for resistance levels
    """
    
    def calculate_pivot_points(high, low, close):
        """计算经典枢轴点位"""
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low  # 压力位1
        r2 = pivot + (high - low)  # 压力位2
        s1 = 2 * pivot - high  # 支撑位1
        s2 = pivot - (high - low)  # 支撑位2
        return [s2, s1], [r1, r2]

    def calculate_volume_profile(df, num_bins=100):
        """计算成交量分布，找出高成交量区域作为支撑压力位"""
        price_range = df['Close'].max() - df['Close'].min()
        bin_size = price_range / num_bins
        
        # 创建价格区间
        price_bins = np.arange(df['Close'].min(), df['Close'].max(), bin_size)
        
        # 计算每个价格区间的成交量
        volume_profile = []
        for i in range(len(price_bins)-1):
            mask = (df['Close'] >= price_bins[i]) & (df['Close'] < price_bins[i+1])
            volume = df.loc[mask, 'Volume'].sum()
            volume_profile.append((price_bins[i], volume))
        
        # 按成交量排序找出高成交量区域
        volume_profile.sort(key=lambda x: x[1], reverse=True)
        total_volume = sum(v for _, v in volume_profile)
        
        # 计算每个价位的成交量占比
        volume_profile = [(price, volume/total_volume) for price, volume in volume_profile]
        
        # 取前20%的高成交量价位
        num_levels = int(len(volume_profile) * 0.2)
        high_volume_prices = sorted(volume_profile[:num_levels])
        
        # 区分支撑位和压力位
        current_price = df['Close'].iloc[-1]
        supports = [(p, v) for p, v in high_volume_prices if p < current_price]
        resistances = [(p, v) for p, v in high_volume_prices if p > current_price]
        
        return supports, resistances

    def calculate_level_strength(price, df):
        """计算支撑/压力位的强度分数 (0-100)，使用专业的技术分析方法
        
        计分项目：
        1. 成交量分析 (35分)
            - 价位成交量占比 (20分)
            - 大单交易占比 (15分)
        2. 价格动量分析 (35分)
            - 反弹/回落力度 (20分)
            - 突破失败次数 (15分)
        3. 时间衰减分析 (20分)
            - 最近触及权重 (12分)
            - 历史形成时间 (8分)
        4. 技术指标确认 (10分)
            - 与其他指标配合 (10分)
        """
        price_threshold = price * 0.005  # 0.5%的价格区间
        
        # 1. 成交量分析 (35分)
        # 1.1 价位成交量占比 (20分)
        volume_around_price = df.loc[abs(df['Close'] - price) <= price_threshold, 'Volume'].sum()
        total_volume = df['Volume'].sum()
        volume_ratio = volume_around_price / total_volume
        volume_score = min(volume_ratio * 200, 20)  # 需要10%的成交量才能得满分
        
        # 1.2 大单交易占比 (15分) - 使用成交额作为替代指标
        amount_around_price = df.loc[abs(df['Close'] - price) <= price_threshold, 'Amount'].sum()
        total_amount = df['Amount'].sum()
        large_trade_ratio = amount_around_price / total_amount
        large_trade_score = min(large_trade_ratio * 150, 15)  # 需要10%的成交额才能得满分
        
        # 2. 价格动量分析 (35分)
        # 2.1 反弹/回落力度 (20分)
        bounces = []
        for i in range(1, len(df)-1):
            if abs(df['Low'].iloc[i] - price) <= price_threshold:
                bounce = (df['High'].iloc[i+1] - df['Low'].iloc[i]) / df['Low'].iloc[i]
                bounces.append(bounce)
        avg_bounce = np.mean(bounces) if bounces else 0
        bounce_score = min(avg_bounce * 400, 20)  # 需要5%的平均反弹幅度才能得满分
        
        # 2.2 突破失败次数 (15分)
        failed_breakouts = 0
        for i in range(1, len(df)-1):
            if (abs(df['Low'].iloc[i] - price) <= price_threshold and 
                df['Close'].iloc[i] > price and 
                df['Close'].iloc[i+1] < price):
                failed_breakouts += 1
        breakout_score = min(failed_breakouts * 3, 15)  # 每次失败突破3分，最高15分
        
        # 3. 时间衰减分析 (20分)
        # 3.1 最近触及权重 (12分)
        recent_touches = 0
        for i in range(max(0, len(df)-20), len(df)):  # 最近20个交易日
            if abs(df['Close'].iloc[i] - price) <= price_threshold:
                recent_touches += 1
        recency_score = min(recent_touches * 3, 12)  # 每次近期触及3分，最高12分
        
        # 3.2 历史形成时间 (8分)
        first_touch_idx = None
        for i in range(len(df)):
            if abs(df['Close'].iloc[i] - price) <= price_threshold:
                first_touch_idx = i
                break
        if first_touch_idx is not None:
            history_length = len(df) - first_touch_idx
            history_score = min(history_length / len(df) * 8, 8)
        else:
            history_score = 0
        
        # 4. 技术指标确认 (10分)
        # 4.1 与其他指标配合 (10分)
        indicator_score = 0
        last_idx = len(df) - 1
        
        # RSI确认
        if 'RSI' in df.columns:
            rsi = df['RSI'].iloc[last_idx]
            if (price < df['Close'].iloc[last_idx] and rsi < 30) or \
               (price > df['Close'].iloc[last_idx] and rsi > 70):
                indicator_score += 3
        
        # MACD确认
        if 'MACD' in df.columns and 'Signal' in df.columns:
            macd = df['MACD'].iloc[last_idx]
            signal = df['Signal'].iloc[last_idx]
            if (price < df['Close'].iloc[last_idx] and macd > signal) or \
               (price > df['Close'].iloc[last_idx] and macd < signal):
                indicator_score += 3
        
        # 布林带确认
        if 'BB_UPPER' in df.columns and 'BB_LOWER' in df.columns:
            bb_upper = df['BB_UPPER'].iloc[last_idx]
            bb_lower = df['BB_LOWER'].iloc[last_idx]
            if (price < df['Close'].iloc[last_idx] and abs(price - bb_lower) / price < 0.02) or \
               (price > df['Close'].iloc[last_idx] and abs(price - bb_upper) / price < 0.02):
                indicator_score += 4
        
        # 计算总分
        total_score = round(
            volume_score +        # 成交量占比 (20分)
            large_trade_score +   # 大单交易占比 (15分)
            bounce_score +        # 反弹/回落力度 (20分)
            breakout_score +      # 突破失败次数 (15分)
            recency_score +       # 最近触及权重 (12分)
            history_score +       # 历史形成时间 (8分)
            indicator_score,      # 技术指标确认 (10分)
            2
        )
        
        # 打印详细的得分信息
        print(f"\n价位 {price:.2f} 的强度分数详情:")
        print(f"1. 成交量分析 (35分):")
        print(f"   - 价位成交量占比: {volume_score:.2f}/20分 ({volume_ratio*100:.2f}%)")
        print(f"   - 大单交易占比: {large_trade_score:.2f}/15分 ({large_trade_ratio*100:.2f}%)")
        print(f"2. 价格动量分析 (35分):")
        print(f"   - 反弹/回落力度: {bounce_score:.2f}/20分 (平均{avg_bounce*100:.2f}%)")
        print(f"   - 突破失败次数: {breakout_score:.2f}/15分 ({failed_breakouts}次)")
        print(f"3. 时间衰减分析 (20分):")
        print(f"   - 最近触及权重: {recency_score:.2f}/12分 ({recent_touches}次)")
        print(f"   - 历史形成时间: {history_score:.2f}/8分")
        print(f"4. 技术指标确认: {indicator_score:.2f}/10分")
        print(f"总分: {total_score}/100")
        
        return total_score

    def find_fractals(df, window):
        """寻找分形顶底，作为潜在的支撑压力位"""
        highs = []
        lows = []
        
        # 使用Williams分形理论
        for i in range(window, len(df) - window):
            # 顶分形
            if all(df['High'].iloc[i] > df['High'].iloc[i-window:i]) and \
               all(df['High'].iloc[i] > df['High'].iloc[i+1:i+window+1]):
                highs.append(df['High'].iloc[i])
            
            # 底分形
            if all(df['Low'].iloc[i] < df['Low'].iloc[i-window:i]) and \
               all(df['Low'].iloc[i] < df['Low'].iloc[i+1:i+window+1]):
                lows.append(df['Low'].iloc[i])
        
        return lows, highs

    # 1. 计算最近的枢轴点位
    recent_high = df['High'].iloc[-window:].max()
    recent_low = df['Low'].iloc[-window:].min()
    recent_close = df['Close'].iloc[-1]
    pivot_supports, pivot_resistances = calculate_pivot_points(recent_high, recent_low, recent_close)
    
    # 2. 计算成交量分布支撑压力位
    volume_supports, volume_resistances = calculate_volume_profile(df)
    
    # 3. 计算分形支撑压力位
    fractal_supports, fractal_resistances = find_fractals(df, window)
    
    # 合并所有支撑位和压力位
    all_supports = (
        [(p, 0) for p in pivot_supports] + 
        volume_supports + 
        [(p, 0) for p in fractal_supports]
    )
    all_resistances = (
        [(p, 0) for p in pivot_resistances] + 
        volume_resistances + 
        [(p, 0) for p in fractal_resistances]
    )
    
    def cluster_levels_with_strength(levels, threshold, df):
        """对价位进行聚类并计算强度"""
        if not levels:
            return []
            
        # 按价格排序
        sorted_levels = sorted(levels, key=lambda x: x[0])
        clusters = []
        
        for price, _ in sorted_levels:
            found_cluster = False
            for cluster in clusters:
                if abs(price - np.mean([p for p, _ in cluster])) / np.mean([p for p, _ in cluster]) < threshold:
                    cluster.append((price, 0))
                    found_cluster = True
                    break
            if not found_cluster:
                clusters.append([(price, 0)])
        
        # 计算每个聚类的平均价格和强度分数
        result = []
        for cluster in clusters:
            if len(cluster) >= touch_count:
                avg_price = np.mean([p for p, _ in cluster])
                strength = calculate_level_strength(avg_price, df)
                result.append((avg_price, strength))
        
        return sorted(result, key=lambda x: (-x[1], x[0]))  # 按强度降序，价格升序排序
    
    # 对支撑位和压力位进行聚类并计算强度
    support_levels = cluster_levels_with_strength(all_supports, price_threshold, df)
    resistance_levels = cluster_levels_with_strength(all_resistances, price_threshold, df)
    
    return support_levels, resistance_levels

@st.cache_data(ttl=43200, show_spinner=False)
def get_stock_data(symbol, start_date, end_date):
    """获取股票历史数据"""
    try:
        # 添加预热期
        WARMUP_DAYS = 30  # 技术指标预热期
        warmup_start_date = start_date - timedelta(days=WARMUP_DAYS)
        
        # 获取包含预热期的股票历史数据
        df = ak.stock_zh_a_hist(symbol=symbol, 
                              start_date=warmup_start_date.strftime('%Y%m%d'),
                              end_date=end_date.strftime('%Y%m%d'),
                              adjust="qfq")
        
        if df.empty:
            return pd.DataFrame(), []
            
        # 重命名列
        df = df.rename(columns={
            '日期': 'datetime',
            '开盘': 'Open',
            '收盘': 'Close',
            '最高': 'High',
            '最低': 'Low',
            '成交量': 'Volume',
            '成交额': 'Amount',
            '振幅': 'Amplitude',
            '涨跌幅': 'Change',
            '涨跌额': 'ChangeAmount',
            '换手率': 'Turnover'
        })
        
        # 转换日期列
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # 计算技术指标（使用完整数据包括预热期）
        # 移动平均线
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA30'] = df['Close'].rolling(window=30).mean()
        
        # 乖离率(BIAS)
        df['BIAS5'] = (df['Close'] - df['MA5']) / df['MA5'] * 100
        df['BIAS10'] = (df['Close'] - df['MA10']) / df['MA10'] * 100
        df['BIAS20'] = (df['Close'] - df['MA20']) / df['MA20'] * 100
        
        # 布林带
        df['BB_MIDDLE'] = df['Close'].rolling(window=20).mean()
        df['BB_UPPER'] = df['BB_MIDDLE'] + 2 * df['Close'].rolling(window=20).std()
        df['BB_LOWER'] = df['BB_MIDDLE'] - 2 * df['Close'].rolling(window=20).std()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal']
        
        # KDJ
        low_min = df['Low'].rolling(window=9).min()
        high_max = df['High'].rolling(window=9).max()
        df['RSV'] = (df['Close'] - low_min) / (high_max - low_min) * 100
        df['K'] = df['RSV'].rolling(window=3).mean()
        df['D'] = df['K'].rolling(window=3).mean()
        df['J'] = 3 * df['K'] - 2 * df['D']

        # 计算支撑位和压力位
        print(f"\n开始计算支撑位和压力位...")
        support_levels, resistance_levels = calculate_support_resistance(
            df,
            window=20,           # 增大窗口以找到更稳定的局部极值
            price_threshold=0.02, # 增大价格聚类阈值以便于形成聚类
            touch_count=2        # 降低触及次数要求
        )
        
        print(f"初始计算结果:")
        print(f"- 支撑位数量: {len(support_levels)}")
        print(f"- 压力位数量: {len(resistance_levels)}")
        if len(support_levels) > 0:
            print(f"- 支撑位 (价格 | 强度分数):")
            for price, strength in support_levels:
                print(f"  - {round(price, 2)} | {strength}/100")
        if len(resistance_levels) > 0:
            print(f"- 压力位 (价格 | 强度分数):")
            for price, strength in resistance_levels:
                print(f"  - {round(price, 2)} | {strength}/100")
        
        # 过滤掉当前价格附近的支撑位和压力位
        current_price = df['Close'].iloc[-1]
        price_range = df['Close'].max() - df['Close'].min()
        threshold = price_range * 0.01  # 1% 的价格范围

        print(f"\n过滤条件:")
        print(f"- 当前价格: {round(current_price, 2)}")
        print(f"- 价格范围: {round(price_range, 2)}")
        print(f"- 过滤阈值: {round(threshold, 2)}")

        # 只保留当前价格上方的压力位和下方的支撑位
        resistance_levels = [(price, strength) for price, strength in resistance_levels 
                           if price > current_price + threshold]
        support_levels = [(price, strength) for price, strength in support_levels 
                         if price < current_price - threshold]

        print(f"\n过滤后结果:")
        print(f"- 支撑位数量: {len(support_levels)}")
        print(f"- 压力位数量: {len(resistance_levels)}")
        if len(support_levels) > 0:
            print(f"- 支撑位 (价格 | 强度分数):")
            for price, strength in support_levels:
                print(f"  - {round(price, 2)} | {strength}/100")
        if len(resistance_levels) > 0:
            print(f"- 压力位 (价格 | 强度分数):")
            for price, strength in resistance_levels:
                print(f"  - {round(price, 2)} | {strength}/100")

        # 只保留最近的几个支撑位和压力位（按强度排序）
        resistance_levels = resistance_levels[:3] if resistance_levels else []
        support_levels = support_levels[-3:] if support_levels else []

        print(f"\n最终结果:")
        print(f"- 支撑位数量: {len(support_levels)}")
        print(f"- 压力位数量: {len(resistance_levels)}")
        if len(support_levels) > 0:
            print(f"- 支撑位 (价格 | 强度分数):")
            for price, strength in support_levels:
                print(f"  - {round(price, 2)} | {strength}/100")
        if len(resistance_levels) > 0:
            print(f"- 压力位 (价格 | 强度分数):")
            for price, strength in resistance_levels:
                print(f"  - {round(price, 2)} | {strength}/100")

        # 转换为列表格式存储在DataFrame中
        df['support_levels'] = [[price for price, _ in support_levels]] * len(df)
        df['resistance_levels'] = [[price for price, _ in resistance_levels]] * len(df)
        df['support_strengths'] = [[strength for _, strength in support_levels]] * len(df)
        df['resistance_strengths'] = [[strength for _, strength in resistance_levels]] * len(df)
        
        # 移除预热期数据，只保留请求的日期范围
        df = df[df['datetime'] >= pd.Timestamp(start_date)]
        
        # 获取交易日历
        trade_cal = df['datetime'].tolist()
        
        return df, trade_cal
    
    except Exception as e:
        print(f"Error getting stock data: {e}")
        return pd.DataFrame(), [] 