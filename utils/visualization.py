import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import akshare as ak
from datetime import datetime

def plot_stock_analysis(df_plot, symbol, trade_cal):
    """Create interactive stock analysis plot using Plotly"""
    
    # Create figure with secondary y-axis
    fig = make_subplots(rows=5, cols=1,
                       shared_xaxes=True,
                       vertical_spacing=0.02,
                       row_heights=[0.4, 0.15, 0.15, 0.15, 0.15])

    # Add candlestick
    fig.add_trace(go.Candlestick(
        x=df_plot['datetime'],
        open=df_plot['Open'],
        high=df_plot['High'],
        low=df_plot['Low'],
        close=df_plot['Close'],
        name='Price',
        increasing_line_color='red',     
        decreasing_line_color='green',   
        increasing_fillcolor='red',      
        decreasing_fillcolor='green'     
    ), row=1, col=1)

    # Add MA lines
    fig.add_trace(go.Scatter(
        x=df_plot['datetime'], 
        y=df_plot['MA5'],
        name=f'MA5: {df_plot["MA5"].iloc[-1]:.2f}',
        line=dict(color='#1f77b4', width=1)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df_plot['datetime'], 
        y=df_plot['MA10'],
        name=f'MA10: {df_plot["MA10"].iloc[-1]:.2f}',
        line=dict(color='#2ca02c', width=1)  # 使用绿色
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df_plot['datetime'], 
        y=df_plot['MA20'],
        name=f'MA20: {df_plot["MA20"].iloc[-1]:.2f}',
        line=dict(color='#ff7f0e', width=1)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df_plot['datetime'], 
        y=df_plot['MA30'],
        name=f'MA30: {df_plot["MA30"].iloc[-1]:.2f}',
        line=dict(color='#d62728', width=1)  # 使用红色
    ), row=1, col=1)

    # Add Bollinger Bands
    fig.add_trace(go.Scatter(
        x=df_plot['datetime'], 
        y=df_plot['BB_UPPER'],
        name='BB Upper',
        line=dict(color='rgba(128, 170, 255, 0.9)', width=1, dash='dot'),  # 更深的蓝色，更高的不透明度
        opacity=0.6  # 提高整体不透明度
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df_plot['datetime'], 
        y=df_plot['BB_LOWER'],
        name='BB Lower',
        line=dict(color='rgba(128, 170, 255, 0.9)', width=1, dash='dot'),  # 更深的蓝色，更高的不透明度
        fill='tonexty',
        fillcolor='rgba(191, 213, 255, 0.3)',  # 稍微加深填充色
        opacity=0.6  # 提高整体不透明度
    ), row=1, col=1)

    # Add support and resistance levels visualization
    if 'support_levels' in df_plot.columns and 'resistance_levels' in df_plot.columns:
        print("\n开始绘制支撑位和压力位...")
        support_levels = df_plot['support_levels'].iloc[0]
        resistance_levels = df_plot['resistance_levels'].iloc[0]
        support_strengths = df_plot['support_strengths'].iloc[0] if 'support_strengths' in df_plot.columns else None
        resistance_strengths = df_plot['resistance_strengths'].iloc[0] if 'resistance_strengths' in df_plot.columns else None
        
        print(f"从数据中获取到:")
        print(f"- 支撑位: {[round(x, 2) for x in support_levels] if support_levels else '无'}")
        print(f"- 压力位: {[round(x, 2) for x in resistance_levels] if resistance_levels else '无'}")
        
        # 创建支撑压力位的可视化
        current_price = df_plot['Close'].iloc[-1]
        
        # 添加支撑位水平线
        for i, level in enumerate(support_levels):
            strength = support_strengths[i] if support_strengths else 50
            
            # 计算强度相关的视觉属性
            line_width = 1 + (strength / 25)  # 强度50分时线宽2，100分时线宽5
            opacity = 0.3 + (strength / 200)  # 强度50分时透明度0.55，100分时透明度0.8
            
            # 添加支撑位水平线
            fig.add_trace(go.Scatter(
                x=df_plot['datetime'],
                y=[level] * len(df_plot),
                name=f'支撑位 {level:.2f}',
                line=dict(
                    color='green',
                    width=line_width,
                    dash='dot'
                ),
                opacity=opacity,
                showlegend=False
            ), row=1, col=1)
            
            # 添加标签
            if strength >= 60:
                label_prefix = "强支撑: "
                font_weight = "bold"
            else:
                label_prefix = "支撑: "
                font_weight = "normal"
                
            fig.add_annotation(
                x=df_plot['datetime'].iloc[-1],
                y=level,
                text=f"{label_prefix}{level:.2f} (强度: {strength:.1f}/100)",
                xref="x",
                yref="y",
                showarrow=False,
                xanchor="left",
                yanchor="middle",
                font=dict(
                    size=10,
                    color="green",
                    family="Arial",
                    weight=font_weight
                )
            )
        
        # 添加压力位水平线
        for i, level in enumerate(resistance_levels):
            strength = resistance_strengths[i] if resistance_strengths else 50
            
            # 计算强度相关的视觉属性
            line_width = 1 + (strength / 25)
            opacity = 0.3 + (strength / 200)
            
            # 添加压力位水平线
            fig.add_trace(go.Scatter(
                x=df_plot['datetime'],
                y=[level] * len(df_plot),
                name=f'压力位 {level:.2f}',
                line=dict(
                    color='red',
                    width=line_width,
                    dash='dot'
                ),
                opacity=opacity,
                showlegend=False
            ), row=1, col=1)
            
            # 添加标签
            if strength >= 60:
                label_prefix = "强压力: "
                font_weight = "bold"
            else:
                label_prefix = "压力: "
                font_weight = "normal"
                
            fig.add_annotation(
                x=df_plot['datetime'].iloc[-1],
                y=level,
                text=f"{label_prefix}{level:.2f} (强度: {strength:.1f}/100)",
                xref="x",
                yref="y",
                showarrow=False,
                xanchor="left",
                yanchor="middle",
                font=dict(
                    size=10,
                    color="red",
                    family="Arial",
                    weight=font_weight
                )
            )
        
        # 添加当前价格线
        fig.add_trace(go.Scatter(
            x=df_plot['datetime'],
            y=[current_price] * len(df_plot),
            name='当前价格',
            line=dict(
                color='blue',
                width=1,
                dash='solid'
            ),
            opacity=0.8,
            showlegend=False
        ), row=1, col=1)
        
        # 添加当前价格标签
        fig.add_annotation(
            x=df_plot['datetime'].iloc[-1],
            y=current_price,
            text=f"当前价格: {current_price:.2f}",
            xref="x",
            yref="y",
            showarrow=False,
            xanchor="left",
            yanchor="middle",
            font=dict(
                size=10,
                color="blue"
            )
        )

    # Add Volume bars
    volume_colors = ['red' if row['Close'] >= row['Open'] else 'green' 
                    for _, row in df_plot.iterrows()]
    
    fig.add_trace(go.Bar(
        x=df_plot['datetime'],
        y=df_plot['Volume'],
        name='Volume',
        marker=dict(
            color=volume_colors,
            line=dict(color=volume_colors)
        ),
        opacity=0.8
    ), row=2, col=1)

    # Add RSI
    fig.add_trace(go.Scatter(
        x=df_plot['datetime'],
        y=df_plot['RSI'],
        name='RSI',
        line=dict(color='purple', width=1)
    ), row=3, col=1)

    # Add RSI lines
    fig.add_hline(y=70, line_dash="dash", line_color="red", 
                  line_width=1, opacity=0.5, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", 
                  line_width=1, opacity=0.5, row=3, col=1)

    # Add MACD histogram
    macd_colors = ['green' if val < 0 else 'red' for val in df_plot['MACD_Hist']]
    fig.add_trace(go.Bar(
        x=df_plot['datetime'],
        y=df_plot['MACD_Hist'],
        marker_color=macd_colors,
        opacity=0.8,
        showlegend=False,
        name=""  # 使用空字符串代替None
    ), row=4, col=1)

    # Add MACD
    fig.add_trace(go.Scatter(
        x=df_plot['datetime'],
        y=df_plot['MACD'],
        line=dict(color='#1f77b4', width=1),
        showlegend=False,
        name=""
    ), row=4, col=1)
    
    fig.add_trace(go.Scatter(
        x=df_plot['datetime'],
        y=df_plot['Signal'],
        line=dict(color='#ff7f0e', width=1),
        showlegend=False,
        name=""
    ), row=4, col=1)

    # Add BIAS
    fig.add_trace(go.Scatter(
        x=df_plot['datetime'],
        y=df_plot['BIAS5'],
        name='BIAS5',
        line=dict(color='#1f77b4', width=1)
    ), row=5, col=1)

    fig.add_trace(go.Scatter(
        x=df_plot['datetime'],
        y=df_plot['BIAS10'],
        name='BIAS10',
        line=dict(color='#2ca02c', width=1)
    ), row=5, col=1)

    fig.add_trace(go.Scatter(
        x=df_plot['datetime'],
        y=df_plot['BIAS20'],
        name='BIAS20',
        line=dict(color='#ff7f0e', width=1)
    ), row=5, col=1)

    # Add BIAS reference lines
    fig.add_hline(y=6, line_dash="dash", line_color="red", 
                  line_width=1, opacity=0.5, row=5, col=1)
    fig.add_hline(y=-6, line_dash="dash", line_color="green", 
                  line_width=1, opacity=0.5, row=5, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color="gray", 
                  line_width=1, opacity=0.3, row=5, col=1)

    # Get non-trading days
    if trade_cal is not None:
        date_range = pd.date_range(start=df_plot['datetime'].min(), end=df_plot['datetime'].max())
        non_trading_days = [d for d in date_range if d not in trade_cal]
    else:
        non_trading_days = []

    # Configure axes
    for i in range(1, 6):
        # 获取实际的交易日期列表
        trading_dates = df_plot['datetime'].sort_values().unique()
        # 每15个交易日取一个点
        tick_dates = trading_dates[::15]
        
        fig.update_xaxes(
            row=i,
            col=1,
            tickformat="%Y/%m/%d",  # 使用完整的年月日格式
            tickangle=0,  # 水平显示
            tickmode='array',  # 使用数组模式来自定义刻度位置
            ticktext=[d.strftime("%Y/%m/%d") for d in tick_dates],  # 显示完整日期
            tickvals=tick_dates,  # 使用选定的交易日作为刻度位置
            rangebreaks=[
                dict(bounds=["sat", "mon"]),
                dict(values=non_trading_days)
            ],
            type="date",
            range=[df_plot['datetime'].min() - pd.Timedelta(days=1),
                  df_plot['datetime'].max() + pd.Timedelta(days=1)],
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='rgba(128, 128, 128, 0.3)',
            zeroline=False
        )

    # Update y-axes labels and ranges
    fig.update_yaxes(title_text="Price", row=1, col=1, 
                    showgrid=False,  # 移除网格
                    showline=True,
                    linewidth=1,
                    linecolor='rgba(128, 128, 128, 0.3)',
                    zeroline=False)
    fig.update_yaxes(title_text="Volume", row=2, col=1,
                    showgrid=False,
                    showline=True,
                    linewidth=1,
                    linecolor='rgba(128, 128, 128, 0.3)',
                    zeroline=False)
    fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100],
                    showgrid=False,
                    showline=True,
                    linewidth=1,
                    linecolor='rgba(128, 128, 128, 0.3)',
                    zeroline=False)
    fig.update_yaxes(title_text="MACD", row=4, col=1,
                    showgrid=False,
                    showline=True,
                    linewidth=1,
                    linecolor='rgba(128, 128, 128, 0.3)',
                    zeroline=False)
    fig.update_yaxes(title_text="BIAS(%)", row=5, col=1,
                    showgrid=False,
                    showline=True,
                    linewidth=1,
                    linecolor='rgba(128, 128, 128, 0.3)',
                    zeroline=False)

    # Update layout
    fig.update_layout(
        title=dict(
            text=f'{symbol} {get_stock_name(symbol)} 价格分析 ({df_plot["datetime"].min().strftime("%Y/%m/%d")} - {df_plot["datetime"].max().strftime("%Y/%m/%d")})',
            x=0.5,
            y=0.98,
            xanchor='center',
            yanchor='top',
            font=dict(size=16)
        ),
        xaxis_rangeslider_visible=False,
        height=1000,
        showlegend=True,  # 启用图例
        legend=dict(
            orientation="h",     # 水平布局
            yanchor="bottom",    # 底部对齐
            y=1.00,             # 位置调整到标题下方
            xanchor="center",    # 居中对齐
            x=0.5,              # 居中位置
            bgcolor='rgba(255, 255, 255, 0.8)',  # 半透明白色背景
            bordercolor='rgba(128, 128, 128, 0.3)',  # 浅灰色边框
            borderwidth=1,
            itemwidth=30,  # 设置图例项的宽度
            itemsizing='constant'  # 保持图例项大小一致
        ),
        margin=dict(t=80, l=50, r=150, b=50),
        plot_bgcolor='white',
        paper_bgcolor='white',
        modebar=dict(
            remove=["zoom", "pan", "select", "lasso", "zoomIn", "zoomOut", 
                   "autoScale", "resetScale", "toImage", "resetViews", 
                   "toggleSpikelines", "hoverClosestCartesian", 
                   "hoverCompareCartesian"]
        )
    )

    # 只显示均线的图例，隐藏其他图例
    for trace in fig.data:
        if trace.name.startswith('MA'):
            trace.showlegend = True
            # 确保线条样式在图例中正确显示
            if 'line' in trace:
                trace.line.update(width=2)  # 增加图例中线条的宽度使其更明显
        else:
            trace.showlegend = False

    return fig

def plot_sector_heatmap(sector_df, max_display=None):
    """Create an enhanced heatmap for sector performance"""
    if sector_df is None or sector_df.empty:
        return None
        
    try:
        # 确保数据框包含必要的列
        required_columns = ['板块名称', '涨跌幅']
        if not all(col in sector_df.columns for col in required_columns):
            rename_map = {}
            for col in sector_df.columns:
                if '名称' in col or '板块' in col:
                    rename_map[col] = '板块名称'
                elif '涨跌' in col and '%' not in col:
                    rename_map[col] = '涨跌幅'
            sector_df = sector_df.rename(columns=rename_map)
        
        # 计算涨跌幅分布
        total_sectors = len(sector_df)
        up_count = len(sector_df[sector_df['涨跌幅'] > 0])
        down_count = len(sector_df[sector_df['涨跌幅'] < 0])
        flat_count = total_sectors - up_count - down_count
        
        # 创建子图布局
        fig = make_subplots(
            rows=3, cols=2,
            specs=[
                [{"colspan": 2}, None],  # 热力图标题
                [{"colspan": 2}, None],  # 板块热力图
                [{"type": "xy"}, {"type": "xy"}]  # 两个柱状图
            ],
            subplot_titles=(
                "",
                "板块涨跌分布",
                "涨跌统计",
                "强度分布"
            ),
            vertical_spacing=0.08,
            row_heights=[0.05, 0.75, 0.2]
        )
        
        # 优化布局：使用16列，使显示更紧凑
        n_cols = 16  # 每行显示的数量
        n_rows = (len(sector_df) + n_cols - 1) // n_cols
        
        # 准备数据
        data = [[None] * n_cols for _ in range(n_rows)]
        names = [['' for _ in range(n_cols)] for _ in range(n_rows)]
        
        # 按涨跌幅排序，确保涨跌幅最大的在左上角
        sector_df = sector_df.sort_values('涨跌幅', ascending=False)
        
        # 从左上角开始填充数据
        for idx, (_, sector) in enumerate(sector_df.iterrows()):
            row = idx // n_cols
            col = idx % n_cols
            data[row][col] = sector['涨跌幅']
            names[row][col] = sector['板块名称']

        # 计算最大绝对涨跌幅用于颜色比例尺
        max_abs_change = max(abs(sector_df['涨跌幅'].max()), abs(sector_df['涨跌幅'].min()))
        
        fig.add_trace(
            go.Heatmap(
                z=data,
                text=[[f"{names[i][j]}<br>{data[i][j]:.2f}%" 
                       if data[i][j] is not None else "" 
                       for j in range(n_cols)] for i in range(n_rows)],
                texttemplate="%{text}",
                textfont={"size": 8},  # 减小字体大小
                colorscale=[
                    [0, 'rgb(0,102,0)'],          # 深绿
                    [0.4, 'rgb(144,238,144)'],    # 浅绿
                    [0.5, 'rgb(255,255,255)'],    # 白色
                    [0.6, 'rgb(255,192,192)'],    # 浅红
                    [1, 'rgb(153,0,0)']           # 深红
                ],
                zmid=0,
                zmin=-max_abs_change,
                zmax=max_abs_change,
                showscale=True,
                colorbar=dict(
                    title=dict(
                        text="涨跌幅(%)",
                        side="right"
                    ),
                    tickformat=".1f",
                    len=0.75,  # 调整色标长度
                    y=0.85,    # 调整色标位置
                    yanchor='top'
                ),
                xgap=1,  # 添加列间距
                ygap=1   # 添加行间距
            ),
            row=2, col=1
        )
        
        # 添加涨跌分布柱状图
        fig.add_trace(
            go.Bar(
                x=['上涨', '下跌', '平盘'],
                y=[up_count, down_count, flat_count],
                text=[f"{up_count}个<br>({up_count/total_sectors*100:.1f}%)", 
                     f"{down_count}个<br>({down_count/total_sectors*100:.1f}%)", 
                     f"{flat_count}个<br>({flat_count/total_sectors*100:.1f}%)"],
                textposition='auto',
                marker_color=['red', 'green', 'gray'],
                showlegend=False
            ),
            row=3, col=1
        )
        
        # 添加强度分布柱状图
        strength_ranges = ['强势(>3%)', '中强(1-3%)', '弱势(<1%)']
        strong = len(sector_df[sector_df['涨跌幅'].abs() > 3])
        medium = len(sector_df[(sector_df['涨跌幅'].abs() <= 3) & (sector_df['涨跌幅'].abs() > 1)])
        weak = len(sector_df[sector_df['涨跌幅'].abs() <= 1])
        
        fig.add_trace(
            go.Bar(
                x=strength_ranges,
                y=[strong, medium, weak],
                text=[f"{strong}个<br>({strong/total_sectors*100:.1f}%)", 
                     f"{medium}个<br>({medium/total_sectors*100:.1f}%)", 
                     f"{weak}个<br>({weak/total_sectors*100:.1f}%)"],
                textposition='auto',
                marker_color=['rgba(255,0,0,0.7)', 'rgba(255,165,0,0.7)', 'rgba(128,128,128,0.7)'],
                showlegend=False
            ),
            row=3, col=2
        )

        # 更新布局
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        fig.update_layout(
            title=dict(
                text=f"板块涨跌幅热力图 (截至 {current_time})",
                x=0.5,
                y=0.95
            ),
            height=min(800, max(400, n_rows * 50)),  # 动态调整高度
            margin=dict(t=50, l=20, r=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            modebar=dict(
                remove=["zoom", "pan", "select", "lasso", "zoomIn", "zoomOut", 
                       "autoScale", "resetScale", "toImage", "resetViews", 
                       "toggleSpikelines", "hoverClosestCartesian", 
                       "hoverCompareCartesian"]
            )
        )

        # 更新坐标轴
        fig.update_xaxes(showticklabels=False, row=2, col=1)
        fig.update_yaxes(showticklabels=False, row=2, col=1)
        
        # 更新柱状图的坐标轴
        for i in range(2):
            fig.update_xaxes(
                showgrid=False,
                showline=True,
                linewidth=1,
                linecolor='rgba(128, 128, 128, 0.3)',
                row=3, col=i+1
            )
            fig.update_yaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128, 128, 128, 0.1)',
                showline=True,
                linewidth=1,
                linecolor='rgba(128, 128, 128, 0.3)',
                row=3, col=i+1
            )

        return fig
        
    except Exception as e:
        print(f"Error creating sector heatmap: {e}")
        return None

def plot_sector_stocks_heatmap(sector_name, sector_stocks):
    """Plot heatmap for stocks in a sector"""
    if sector_stocks is None or sector_stocks.empty:
        return None
        
    try:
        # 按涨跌幅排序
        stocks_df = sector_stocks.sort_values('涨跌幅', ascending=False)
        
        # 创建热力图数据
        n_cols = 8  # 每行显示的数量
        n_rows = (len(stocks_df) + n_cols - 1) // n_cols
        
        # 准备数据
        data = [[None] * n_cols for _ in range(n_rows)]
        names = [['' for _ in range(n_cols)] for _ in range(n_rows)]
        
        # 从左上角开始填充数据
        for idx in range(len(stocks_df)):
            row = idx // n_cols
            col = idx % n_cols
            data[row][col] = stocks_df.iloc[idx]['涨跌幅']
            names[row][col] = f"{stocks_df.iloc[idx]['名称']}\n{stocks_df.iloc[idx]['最新价']}"

        # 创建自定义颜色刻度
        max_abs_change = max(abs(stocks_df['涨跌幅'].max()), abs(stocks_df['涨跌幅'].min()))
        colorscale = [
            [0, 'rgb(0,102,0)'],          # 深绿
            [0.4, 'rgb(144,238,144)'],    # 浅绿
            [0.5, 'rgb(255,255,255)'],    # 白色
            [0.6, 'rgb(255,192,192)'],    # 浅红
            [1, 'rgb(153,0,0)']           # 深红
        ]

        # 创建热力图
        fig = go.Figure(data=go.Heatmap(
            z=data,
            text=[[f"{names[i][j]}<br>{data[i][j]:.2f}%" 
                   if data[i][j] is not None else "" 
                   for j in range(n_cols)] for i in range(n_rows)],
            texttemplate="%{text}",
            textfont={"size": 10},
            colorscale=colorscale,
            zmid=0,
            zmin=-max_abs_change,
            zmax=max_abs_change,
            showscale=True,
            colorbar=dict(
                title=dict(
                    text="涨跌幅(%)",
                    side="right"
                ),
                tickformat=".1f"
            )
        ))

        # 更新布局
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        fig.update_layout(
            title=dict(
                text=f"{sector_name}板块个股涨跌幅 (截至 {current_time})",
                x=0.5,
                y=0.95
            ),
            height=min(800, max(400, n_rows * 50)),  # 动态调整高度
            margin=dict(t=50, l=20, r=20, b=20),  # 增加顶部边距以适应更长的标题
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False, autorange='reversed'),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            modebar=dict(
                remove=["zoom", "pan", "select", "lasso", "zoomIn", "zoomOut", 
                       "autoScale", "resetScale", "toImage", "resetViews", 
                       "toggleSpikelines", "hoverClosestCartesian", 
                       "hoverCompareCartesian"]
            )
        )

        return fig
        
    except Exception as e:
        print(f"Error creating stocks heatmap: {e}")
        return None 

def get_stock_name(symbol):
    """Get stock name from symbol"""
    try:
        df = ak.stock_info_a_code_name()
        stock_info = df[df['code'] == symbol]
        if not stock_info.empty:
            return stock_info.iloc[0]['name']
        return ''
    except Exception as e:
        print(f"Error getting stock name: {e}")
        return '' 