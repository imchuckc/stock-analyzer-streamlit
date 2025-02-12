import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import akshare as ak
import json

# Import custom modules
from utils.data_fetcher import get_stock_list, get_stock_data, get_sector_stocks
from utils.analysis import analyze_stock, analyze_stock_commentary, analyze_support_resistance
from utils.visualization import plot_stock_analysis, plot_sector_heatmap, plot_sector_stocks_heatmap
from utils.market_overview import get_market_overview
from utils.data_preprocessor import load_sector_data

# 设置页面配置
st.set_page_config(
    layout="wide", 
    page_title="Stock Analysis Tool",
    initial_sidebar_state="collapsed"  # 默认收起侧边栏
)

# 获取交易日历
@st.cache_data(ttl=86400)  # 24小时缓存
def get_trading_calendar():
    """获取最近一年的交易日历"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    try:
        # 获取交易日历
        trade_cal = ak.tool_trade_date_hist_sina()
        trade_cal['trade_date'] = pd.to_datetime(trade_cal['trade_date'])
        # 筛选日期范围内的交易日
        mask = (trade_cal['trade_date'] >= pd.Timestamp(start_date)) & (trade_cal['trade_date'] <= pd.Timestamp(end_date))
        return trade_cal[mask]['trade_date'].tolist()
    except Exception as e:
        print(f"Error getting trading calendar: {e}")
        return []

# 获取交易日历
trading_calendar = get_trading_calendar()

# 直接开始主程序部分
st.title("📈 Stock Analysis Tool")

# 初始化session state
if 'tab_states' not in st.session_state:
    st.session_state.tab_states = {
        "市场概览": {"loaded": False},
        "行业板块分析": {"loaded": False, "selected_sector": None},
        "概念板块分析": {"loaded": False, "selected_sector": None},
        "个股分析工具": {"loaded": False},
        "个股板块归属": {"loaded": False}
    }

# 缓存数据加载函数
@st.cache_data(ttl=14400)  # 4小时缓存
def load_market_data():
    return get_market_overview()

@st.cache_data(ttl=43200)  # 12小时缓存
def load_industry_list():
    try:
        industry_df = ak.stock_board_industry_name_em()
        return industry_df['板块名称'].tolist()
    except Exception as e:
        st.error(f"获取行业板块列表失败: {e}")
        return []

@st.cache_data(ttl=43200)  # 12小时缓存
def load_concept_list():
    try:
        concept_df = ak.stock_board_concept_name_em()
        return concept_df['板块名称'].tolist()
    except Exception as e:
        st.error(f"获取概念板块列表失败: {e}")
        return []

@st.cache_data(ttl=1800)  # 30分钟缓存
def load_sector_stocks(sector_type, sector_name):
    if sector_type == "industry":
        return ak.stock_board_industry_cons_em(symbol=sector_name)
    else:
        return ak.stock_board_concept_cons_em(symbol=sector_name)

def get_stock_info(stock_code):
    file_path = 'data/sector_data.json'
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            stock_data = json.load(f)
        
        # 获取股票信息
        stock_info = stock_data.get('stocks', {}).get(stock_code, None)  # 添加 'stocks' 键的访问
        if stock_info is None:
            st.error(f"未找到股票代码 {stock_code} 的信息")
            return {}  # 返回空字典而不是 None
            
        return stock_info
    except FileNotFoundError:
        st.error(f"找不到数据文件: {file_path}")
        return {}
    except json.JSONDecodeError:
        st.error("数据文件格式错误")
        return {}

def display_stock_selector():
    file_path = 'data/sector_data.json'
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            stock_data = json.load(f)
        
        # 从 'stocks' 键中获取股票列表
        stocks = stock_data.get('stocks', {})
        stock_list = [(code, f"{info['name']}({code})") for code, info in stocks.items()]
        stock_list.sort(key=lambda x: x[0])
        
        selected_stock = st.selectbox(
            "股票代码",
            options=[item[1] for item in stock_list],
            key="stock_selector"
        )
        
        if selected_stock:
            stock_code = selected_stock.split('(')[1].split(')')[0]
            return stock_code
        return None
    except FileNotFoundError:
        st.error(f"找不到数据文件: {file_path}")
        return None
    except json.JSONDecodeError:
        st.error("数据文件格式错误")
        return None

# 创建标签页
tabs = ["市场概览", "行业板块分析", "概念板块分析", "个股分析工具", "个股板块归属"]
current_tab = st.tabs(tabs)

# 在每个tab中显示相应的内容
with current_tab[0]:   # 市场概览
    if not st.session_state.tab_states["市场概览"]["loaded"]:
        index_data, sector_df, concept_df = load_market_data()
        st.session_state.tab_states["市场概览"]["loaded"] = True
        st.session_state.tab_states["市场概览"]["data"] = (index_data, sector_df, concept_df)
    else:
        index_data, sector_df, concept_df = st.session_state.tab_states["市场概览"]["data"]
    
    if index_data:
        # 显示主要指数
        cols = st.columns(len(index_data))
        for col, (name, index) in zip(cols, index_data.items()):
            with col:
                color = "red" if float(index['涨跌幅']) > 0 else "green"
                st.markdown(f"""
                    <div style='text-align: center; padding: 10px; background-color: white; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                        <div style='font-size: 1.1em; font-weight: bold;'>{name}</div>
                        <div style='font-size: 1.2em; color: {color};'>{float(index['最新价']):.2f}</div>
                        <div style='font-size: 0.9em; color: {color};'>{float(index['涨跌幅']):.2f}%</div>
                        <div style='font-size: 0.8em; color: gray;'>成交额: {float(index['成交额'])/100000000:.2f}亿</div>
                    </div>
                """, unsafe_allow_html=True)
    
    # 显示板块热力图
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding: 10px 20px;
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            font-weight: 500;
        }
        .stTabs [aria-selected="true"] {
            background-color: #f0f7ff;
            border-bottom: 2px solid #1f77b4;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 创建行业板块和概念板块的子标签页
    subtab1, subtab2 = st.tabs(["📊 行业板块分布", "🎯 概念板块分布"])
    
    with subtab1:
        if sector_df is not None:
            st.markdown("<br>", unsafe_allow_html=True)
            heatmap_fig = plot_sector_heatmap(sector_df)
            if heatmap_fig:
                st.plotly_chart(heatmap_fig, use_container_width=True, key="sector_heatmap")
        else:
            st.warning("无法获取行业板块数据")
            
    with subtab2:
        if concept_df is not None:
            st.markdown("<br>", unsafe_allow_html=True)
            concept_heatmap_fig = plot_sector_heatmap(concept_df)
            if concept_heatmap_fig:
                st.plotly_chart(concept_heatmap_fig, use_container_width=True, key="concept_heatmap")
        else:
            st.warning("无法获取概念板块数据")

with current_tab[1]:   # 行业板块分析
    if not st.session_state.tab_states["行业板块分析"]["loaded"]:
        industry_list = load_industry_list()
        st.session_state.tab_states["行业板块分析"]["loaded"] = True
        st.session_state.tab_states["行业板块分析"]["list"] = industry_list

    # 添加板块选择框
    selected_sector = st.selectbox(
        "选择行业板块",
        options=st.session_state.tab_states["行业板块分析"]["list"],
        help="选择要分析的行业板块",
        key="industry_sector_select"
    )

    if selected_sector:
        if selected_sector != st.session_state.tab_states["行业板块分析"]["selected_sector"]:
            sector_stocks = load_sector_stocks("industry", selected_sector)
            st.session_state.tab_states["行业板块分析"]["selected_sector"] = selected_sector
            st.session_state.tab_states["行业板块分析"]["stocks"] = sector_stocks
        else:
            sector_stocks = st.session_state.tab_states["行业板块分析"]["stocks"]

        if sector_stocks is not None:
            # 计算涨跌家数
            up_count = len(sector_stocks[sector_stocks['涨跌幅'] > 0])
            down_count = len(sector_stocks[sector_stocks['涨跌幅'] < 0])
            flat_count = len(sector_stocks[sector_stocks['涨跌幅'] == 0])
            
            # 创建两列布局
            col1, col2 = st.columns([3, 1])
            
            with col2:
                # 显示板块统计信息
                st.markdown(f"""
                    <div style='background-color: white; padding: 10px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                        <h4 style='text-align: center; margin-bottom: 10px;'>{selected_sector}统计</h4>
                        <p style='color: red; margin: 5px 0;'>上涨: {up_count}家</p>
                        <p style='color: green; margin: 5px 0;'>下跌: {down_count}家</p>
                        <p style='color: gray; margin: 5px 0;'>平盘: {flat_count}家</p>
                        <p style='margin: 5px 0;'>总计: {len(sector_stocks)}家</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # 创建涨跌幅排名的左右布局
                st.markdown("<br>", unsafe_allow_html=True)
                rank_col1, rank_col2 = st.columns(2)
                
                with rank_col1:
                    # 获取涨幅股票并按涨幅排序
                    gainers = sector_stocks[sector_stocks['涨跌幅'] > 0].sort_values('涨跌幅', ascending=False)
                    if not gainers.empty:
                        st.markdown(f"### 涨幅排名 ({len(gainers)}家)")
                        # 显示前10个涨幅股票
                        for _, stock in gainers.head(10).iterrows():
                            # 添加市场标识
                            market_tag = ""
                            if stock['代码'].startswith('688'):
                                market_tag = "<span style='background-color: #FFE4E1; padding: 1px 4px; border-radius: 3px; font-size: 0.8em;'>科创板</span> "
                            elif stock['代码'].startswith('300'):
                                market_tag = "<span style='background-color: #E6E6FA; padding: 1px 4px; border-radius: 3px; font-size: 0.8em;'>创业板</span> "
                            elif stock['代码'].startswith('8'):
                                market_tag = "<span style='background-color: #F0FFF0; padding: 1px 4px; border-radius: 3px; font-size: 0.8em;'>北交所</span> "
                            
                            st.markdown(f"""
                                <div style='background-color: rgba(255,240,240,0.5); padding: 5px; margin: 2px 0; border-radius: 3px;'>
                                    <span style='color: red;'>{market_tag}{stock['名称']} ({stock['代码']})</span><br>
                                    <small>涨跌幅: <span style='color: red;'>+{stock['涨跌幅']:.2f}%</span></small>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("### 暂无上涨个股")
                
                with rank_col2:
                    # 获取跌幅股票并按跌幅排序
                    losers = sector_stocks[sector_stocks['涨跌幅'] < 0].sort_values('涨跌幅')
                    if not losers.empty:
                        st.markdown(f"### 跌幅排名 ({len(losers)}家)")
                        # 显示前10个跌幅股票
                        for _, stock in losers.head(10).iterrows():
                            # 添加市场标识
                            market_tag = ""
                            if stock['代码'].startswith('688'):
                                market_tag = "<span style='background-color: #FFE4E1; padding: 1px 4px; border-radius: 3px; font-size: 0.8em;'>科创板</span> "
                            elif stock['代码'].startswith('300'):
                                market_tag = "<span style='background-color: #E6E6FA; padding: 1px 4px; border-radius: 3px; font-size: 0.8em;'>创业板</span> "
                            elif stock['代码'].startswith('8'):
                                market_tag = "<span style='background-color: #F0FFF0; padding: 1px 4px; border-radius: 3px; font-size: 0.8em;'>北交所</span> "
                            
                            st.markdown(f"""
                                <div style='background-color: rgba(240,255,240,0.5); padding: 5px; margin: 2px 0; border-radius: 3px;'>
                                    <span style='color: green;'>{market_tag}{stock['名称']} ({stock['代码']})</span><br>
                                    <small>涨跌幅: <span style='color: green;'>{stock['涨跌幅']:.2f}%</span></small>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("### 暂无下跌个股")
            
            with col1:
                # 创建并显示热力图
                fig = plot_sector_stocks_heatmap(selected_sector, sector_stocks)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"industry_stocks_{selected_sector}")
        else:
            st.warning("无法获取行业板块个股数据")

with current_tab[2]:   # 概念板块分析
    if not st.session_state.tab_states["概念板块分析"]["loaded"]:
        concept_list = load_concept_list()
        st.session_state.tab_states["概念板块分析"]["loaded"] = True
        st.session_state.tab_states["概念板块分析"]["list"] = concept_list

    # 添加板块选择框
    selected_sector = st.selectbox(
        "选择概念板块",
        options=st.session_state.tab_states["概念板块分析"]["list"],
        help="选择要分析的概念板块",
        key="concept_sector_select"
    )

    if selected_sector:
        if selected_sector != st.session_state.tab_states["概念板块分析"]["selected_sector"]:
            sector_stocks = load_sector_stocks("concept", selected_sector)
            st.session_state.tab_states["概念板块分析"]["selected_sector"] = selected_sector
            st.session_state.tab_states["概念板块分析"]["stocks"] = sector_stocks
        else:
            sector_stocks = st.session_state.tab_states["概念板块分析"]["stocks"]

        if sector_stocks is not None:
            # 计算涨跌家数
            up_count = len(sector_stocks[sector_stocks['涨跌幅'] > 0])
            down_count = len(sector_stocks[sector_stocks['涨跌幅'] < 0])
            flat_count = len(sector_stocks[sector_stocks['涨跌幅'] == 0])
            
            # 创建两列布局
            col1, col2 = st.columns([3, 1])
            
            with col2:
                # 显示板块统计信息
                st.markdown(f"""
                    <div style='background-color: white; padding: 10px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                        <h4 style='text-align: center; margin-bottom: 10px;'>{selected_sector}统计</h4>
                        <p style='color: red; margin: 5px 0;'>上涨: {up_count}家</p>
                        <p style='color: green; margin: 5px 0;'>下跌: {down_count}家</p>
                        <p style='color: gray; margin: 5px 0;'>平盘: {flat_count}家</p>
                        <p style='margin: 5px 0;'>总计: {len(sector_stocks)}家</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # 创建涨跌幅排名的左右布局
                st.markdown("<br>", unsafe_allow_html=True)
                rank_col1, rank_col2 = st.columns(2)
                
                with rank_col1:
                    # 获取涨幅股票并按涨幅排序
                    gainers = sector_stocks[sector_stocks['涨跌幅'] > 0].sort_values('涨跌幅', ascending=False)
                    if not gainers.empty:
                        st.markdown(f"### 涨幅排名 ({len(gainers)}家)")
                        # 显示前10个涨幅股票
                        for _, stock in gainers.head(10).iterrows():
                            # 添加市场标识
                            market_tag = ""
                            if stock['代码'].startswith('688'):
                                market_tag = "<span style='background-color: #FFE4E1; padding: 1px 4px; border-radius: 3px; font-size: 0.8em;'>科创板</span> "
                            elif stock['代码'].startswith('300'):
                                market_tag = "<span style='background-color: #E6E6FA; padding: 1px 4px; border-radius: 3px; font-size: 0.8em;'>创业板</span> "
                            elif stock['代码'].startswith('8'):
                                market_tag = "<span style='background-color: #F0FFF0; padding: 1px 4px; border-radius: 3px; font-size: 0.8em;'>北交所</span> "
                            
                            st.markdown(f"""
                                <div style='background-color: rgba(255,240,240,0.5); padding: 5px; margin: 2px 0; border-radius: 3px;'>
                                    <span style='color: red;'>{market_tag}{stock['名称']} ({stock['代码']})</span><br>
                                    <small>涨跌幅: <span style='color: red;'>+{stock['涨跌幅']:.2f}%</span></small>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("### 暂无上涨个股")
                
                with rank_col2:
                    # 获取跌幅股票并按跌幅排序
                    losers = sector_stocks[sector_stocks['涨跌幅'] < 0].sort_values('涨跌幅')
                    if not losers.empty:
                        st.markdown(f"### 跌幅排名 ({len(losers)}家)")
                        # 显示前10个跌幅股票
                        for _, stock in losers.head(10).iterrows():
                            # 添加市场标识
                            market_tag = ""
                            if stock['代码'].startswith('688'):
                                market_tag = "<span style='background-color: #FFE4E1; padding: 1px 4px; border-radius: 3px; font-size: 0.8em;'>科创板</span> "
                            elif stock['代码'].startswith('300'):
                                market_tag = "<span style='background-color: #E6E6FA; padding: 1px 4px; border-radius: 3px; font-size: 0.8em;'>创业板</span> "
                            elif stock['代码'].startswith('8'):
                                market_tag = "<span style='background-color: #F0FFF0; padding: 1px 4px; border-radius: 3px; font-size: 0.8em;'>北交所</span> "
                            
                            st.markdown(f"""
                                <div style='background-color: rgba(240,255,240,0.5); padding: 5px; margin: 2px 0; border-radius: 3px;'>
                                    <span style='color: green;'>{market_tag}{stock['名称']} ({stock['代码']})</span><br>
                                    <small>涨跌幅: <span style='color: green;'>{stock['涨跌幅']:.2f}%</span></small>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("### 暂无下跌个股")
                
                with col1:
                    # 创建并显示热力图
                    fig = plot_sector_stocks_heatmap(selected_sector, sector_stocks)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True, key=f"concept_stocks_{selected_sector}")
        else:
            st.warning("无法获取概念板块个股数据")

with current_tab[3]:   # 个股分析工具
    if not st.session_state.tab_states["个股分析工具"]["loaded"]:
        stock_options = get_stock_list()
        st.session_state.tab_states["个股分析工具"]["loaded"] = True
        st.session_state.tab_states["个股分析工具"]["options"] = stock_options
    else:
        stock_options = st.session_state.tab_states["个股分析工具"]["options"]

    # 添加自定义CSS样式
    st.markdown("""
        <style>
        .main .block-container {
            max-width: 1200px;  # 限制最大宽度
            padding-top: 1rem;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 40px;
            padding: 8px 16px;
            background-color: white;
            border-radius: 4px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            font-weight: 500;
            font-size: 0.9rem;
        }
        .market-analysis-container {
            background: white;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .market-analysis-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid #e5e7eb;
        }
        .analysis-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
        }
        .analysis-card {
            padding: 16px;
            border-radius: 6px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            font-size: 0.9rem;
            line-height: 1.5;
        }
        .card-title {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 12px;
            color: #1f2937;
            padding-bottom: 6px;
            border-bottom: 1px solid rgba(0,0,0,0.1);
        }
        .card-content {
            font-size: 0.9rem;
            color: #374151;
            line-height: 1.5;
        }
        .number-highlight {
            color: #dc2626;
            font-weight: 500;
        }
        .price-current {
            color: #1e40af;
            font-weight: 500;
        }
        .price-support {
            color: #059669;
            font-weight: 500;
        }
        .price-resistance {
            color: #dc2626;
            font-weight: 500;
        }
        /* Technical Grid Styles */
        .technical-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: auto auto;
            gap: 15px;
            padding: 10px;
        }
        .technical-item {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 8px;
            padding: 15px;
            border: 1px solid rgba(0, 0, 0, 0.05);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .technical-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
        }
        .technical-subtitle {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 10px;
            padding-bottom: 6px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        }
        .technical-content {
            font-size: 0.9rem;
            color: #374151;
            line-height: 1.5;
        }
        .rsi .technical-subtitle { 
            color: #ef4444;
        }
        .bias .technical-subtitle { 
            color: #10b981;
        }
        .macd .technical-subtitle { 
            color: #3b82f6;
        }
        .boll .technical-subtitle { 
            color: #8b5cf6;
        }
        .rsi { 
            border-top: 3px solid #ef4444;
        }
        .bias { 
            border-top: 3px solid #10b981;
        }
        .macd { 
            border-top: 3px solid #3b82f6;
        }
        .boll { 
            border-top: 3px solid #8b5cf6;
        }
        </style>
    """, unsafe_allow_html=True)

    # 创建更紧凑的输入区域
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        symbol_display = st.selectbox(
            "股票代码",
            options=list(stock_options.keys()),
            index=0,
            help="搜索或选择股票代码"
        )
        symbol = stock_options[symbol_display]

    with col2:
        trading_days = st.slider(
            "分析周期(交易日)", 
            min_value=20, 
            max_value=250, 
            value=60, 
            step=10,
            help="选择要分析的交易日数量"
        )

    with col3:
        st.write("")  # 空行对齐
        st.write("")  # 空行对齐
        analyze_button = st.button("开始分析", type="primary")

    if analyze_button:
        # 根据交易日数量计算开始日期
        end_date = datetime.now()
        if trading_calendar:
            # 从当前日期向前数trading_days个交易日
            available_dates = [d for d in trading_calendar if d <= end_date]
            if len(available_dates) >= trading_days:
                start_date = available_dates[-trading_days]
            else:
                start_date = available_dates[0]
        else:
            # 如果无法获取交易日历，使用近似值
            start_date = end_date - timedelta(days=int(trading_days * 1.4))  # 大约考虑周末和节假日
        
        with st.spinner('Loading and analyzing data...'):
            df, trade_cal = get_stock_data(symbol, start_date, end_date)
            
            if df.empty:
                st.error("No data available for the selected date range")
                st.stop()

            # Prepare plot data
            df_plot = df.copy()
            
            # 创建容器和列布局
            main_container = st.container()
            
            with main_container:
                # 创建6:4布局的两列
                left_col, right_col = st.columns([6, 4])
                
                with left_col:
                    # 创建并显示图表
                    fig = plot_stock_analysis(df_plot, symbol, trade_cal)
                    st.plotly_chart(fig, use_container_width=True, key=f"stock_analysis_{symbol}")
                
                with right_col:
                    # 获取分析结果
                    commentary = analyze_stock_commentary(df_plot)
                    
                    # 将评论分成不同部分
                    technical_analysis_content = []
                    volume_price_content = []
                    moving_average_content = []
                    
                    current_section = None
                    for line in commentary:
                        if "技术指标分析" in line:
                            current_section = technical_analysis_content
                        elif "量价分析" in line:
                            current_section = volume_price_content
                        elif "均线系统分析" in line:
                            current_section = moving_average_content
                        elif current_section is not None and line.strip():  # 只添加非空行
                            current_section.append(line)
                    
                    # 技术指标分析卡片
                    # 将各个指标的内容分别收集
                    rsi_content = []
                    bias_content = []
                    macd_content = []
                    boll_content = []
                    
                    # 分类处理technical_analysis_content中的内容
                    current_section = None
                    for line in technical_analysis_content:
                        if "RSI指标" in line:
                            current_section = rsi_content
                        elif "乖离率分析" in line:
                            current_section = bias_content
                        elif "MACD指标" in line:
                            current_section = macd_content
                        elif "布林带分析" in line:
                            current_section = boll_content
                        elif current_section is not None and line.strip():
                            current_section.append(line)
                    
                    # 支撑压力分析卡片
                    st.markdown("""
                        <div class="analysis-card support-resistance">
                            <div class="card-title">🎯 支撑压力分析</div>
                            <div class="card-content">
                    """, unsafe_allow_html=True)
                    st.markdown(analyze_support_resistance(df_plot), unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)
                    
                    # 技术指标分析卡片
                    # 将各个指标的内容分别收集
                    rsi_content = []
                    bias_content = []
                    macd_content = []
                    boll_content = []
                    
                    # 分类处理technical_analysis_content中的内容
                    current_section = None
                    for line in technical_analysis_content:
                        if "RSI指标" in line:
                            current_section = rsi_content
                        elif "乖离率分析" in line:
                            current_section = bias_content
                        elif "MACD指标" in line:
                            current_section = macd_content
                        elif "布林带分析" in line:
                            current_section = boll_content
                        elif current_section is not None and line.strip():
                            current_section.append(line)
                    
                    # 创建2x2网格布局的HTML
                    technical_grid_html = f"""
                        <div class="analysis-card technical">
                            <div class="card-title">📊 技术指标分析</div>
                            <div class="technical-grid">
                                <div class="technical-item rsi">
                                    <div class="technical-subtitle">RSI指标</div>
                                    <div class="technical-content">
                                        {'<br>'.join(rsi_content)}
                                    </div>
                                </div>
                                <div class="technical-item bias">
                                    <div class="technical-subtitle">乖离率分析</div>
                                    <div class="technical-content">
                                        {'<br>'.join(bias_content)}
                                    </div>
                                </div>
                                <div class="technical-item macd">
                                    <div class="technical-subtitle">MACD指标</div>
                                    <div class="technical-content">
                                        {'<br>'.join(macd_content)}
                                    </div>
                                </div>
                                <div class="technical-item boll">
                                    <div class="technical-subtitle">布林带分析</div>
                                    <div class="technical-content">
                                        {'<br>'.join(boll_content)}
                                    </div>
                                </div>
                            </div>
                        </div>
                    """
                    
                    # 渲染技术指标网格
                    st.markdown(technical_grid_html, unsafe_allow_html=True)
                    
                    # 量价分析卡片
                    st.markdown("""
                        <div class="analysis-card volume-price">
                            <div class="card-title">📈 量价分析</div>
                            <div class="card-content">
                    """, unsafe_allow_html=True)
                    st.markdown("<br>".join(volume_price_content), unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)
                    
                    # 均线系统分析卡片
                    st.markdown("""
                        <div class="analysis-card moving-average">
                            <div class="card-title">📉 均线系统分析</div>
                            <div class="card-content">
                    """, unsafe_allow_html=True)
                    st.markdown("<br>".join(moving_average_content), unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)
                    
                    st.markdown("</div></div>", unsafe_allow_html=True)

with current_tab[4]:   # 个股板块归属
    if not st.session_state.tab_states.get("个股板块归属"):
        st.session_state.tab_states["个股板块归属"] = {"loaded": False}
    
    if not st.session_state.tab_states["个股板块归属"]["loaded"]:
        stock_options = get_stock_list()
        st.session_state.tab_states["个股板块归属"]["loaded"] = True
        st.session_state.tab_states["个股板块归属"]["options"] = stock_options
    else:
        stock_options = st.session_state.tab_states["个股板块归属"]["options"]

    # 创建更紧凑的输入区域
    col1, col2 = st.columns([3, 1])
    
    with col1:
        symbol_display = st.selectbox(
            "股票代码",
            options=list(stock_options.keys()),
            index=0,
            help="搜索或选择股票代码",
            key="sector_stock_select"
        )
        symbol = stock_options[symbol_display]

    with col2:
        st.write("")  # 空行对齐
        st.write("")  # 空行对齐
        analyze_button = st.button("查看板块归属", type="primary", key="sector_analyze_button")

    if analyze_button:
        with st.spinner('正在获取板块信息...'):
            sector_info = get_stock_info(symbol)
            
            # 显示行业信息
            st.markdown("""
                <div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                    <h3 style='color: #1f2937; margin-bottom: 15px;'>🏭 所属行业</h3>
            """, unsafe_allow_html=True)
            
            if sector_info.get('industry'):
                for industry in sector_info['industry']:
                    st.markdown(f"""
                        <div style='background-color: #f3f4f6; margin: 5px 0; padding: 10px; border-radius: 5px;'>
                            {industry}
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("暂无行业归属信息")
            
            # 显示概念信息
            st.markdown("""
                <div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 20px;'>
                    <h3 style='color: #1f2937; margin-bottom: 15px;'>💡 所属概念</h3>
            """, unsafe_allow_html=True)
            
            if sector_info.get('concept'):
                # 创建网格布局显示概念
                cols = st.columns(3)
                for i, concept in enumerate(sector_info['concept']):
                    with cols[i % 3]:
                        st.markdown(f"""
                            <div style='background-color: #f3f4f6; margin: 5px 0; padding: 10px; border-radius: 5px;'>
                                {concept}
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("暂无概念归属信息")
            
            st.markdown("</div>", unsafe_allow_html=True)

# 在侧边栏添加缓存控制
with st.sidebar:
    st.write("### 数据缓存控制")
    if st.button("清除所有缓存数据"):
        st.cache_data.clear()
        st.success("✅ 缓存已清除！")
    
    # 显示数据更新时间
    st.write("### 数据更新时间")
    st.info(f"""
        - 市场概览: 4小时更新一次
        - 板块数据: 12小时更新一次
        - 个股数据: 8小时更新一次
        - 股票列表: 24小时更新一次
        
        最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)

    # 添加交易时段提示
    now = datetime.now()
    is_trading_time = (
        now.weekday() < 5 and  # 周一到周五
        ((now.hour == 9 and now.minute >= 30) or  # 9:30-11:30
         (now.hour == 10) or
         (now.hour == 11 and now.minute <= 30) or
         (now.hour >= 13 and now.hour < 15))  # 13:00-15:00
    )
    
    if is_trading_time:
        st.warning("⚠️ 当前为交易时段，数据更新较频繁")
    else:
        st.success("📊 当前为非交易时段，使用缓存数据") 