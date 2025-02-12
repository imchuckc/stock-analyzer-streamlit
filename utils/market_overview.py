import akshare as ak
import pandas as pd
from datetime import datetime

def get_market_overview():
    """获取市场概览数据"""
    try:
        # 获取指数数据
        indices = {
            '上证指数': 'sh000001',
            '深证成指': 'sz399001',
            '创业板指': 'sz399006',
            '科创50': 'sh000688',
            '上证50': 'sh000016',
            '沪深300': 'sh000300',
            '中证500': 'sh000905',
            '中证1000': 'sh000852'
        }
        
        market_data = {}
        for name, code in indices.items():
            try:
                # 使用 stock_zh_index_daily_em 替代 stock_zh_index_spot
                df = ak.stock_zh_index_daily_em(symbol=code)
                if not df.empty:
                    # 计算涨跌幅
                    df['pct_change'] = (df['close'] - df['close'].shift(1)) / df['close'].shift(1) * 100
                    latest = df.iloc[-1]
                    market_data[name] = {
                        '最新价': latest['close'],
                        '涨跌幅': latest['pct_change'],
                        '成交额': latest['amount']
                    }
            except Exception as e:
                print(f"Error getting index data for {name}: {e}")
                continue  # 如果获取某个指数失败，继续获取下一个
        
        # 获取行业板块数据
        try:
            sector_df = ak.stock_board_industry_name_em()
            if not sector_df.empty:
                # 按涨跌幅排序
                sector_df = sector_df.sort_values('涨跌幅', ascending=False)
        except Exception as e:
            print(f"Error getting sector data: {e}")
            sector_df = None
            
        # 获取概念板块数据
        try:
            concept_df = ak.stock_board_concept_name_em()
            if not concept_df.empty:
                # 按涨跌幅排序
                concept_df = concept_df.sort_values('涨跌幅', ascending=False)
                
                # 计算统计信息
                total_concepts = len(concept_df)
                up_count = len(concept_df[concept_df['涨跌幅'] > 0])
                down_count = len(concept_df[concept_df['涨跌幅'] < 0])
                flat_count = len(concept_df[concept_df['涨跌幅'] == 0])
                
                # 添加统计信息到DataFrame的属性中
                concept_df.attrs['statistics'] = {
                    'total': total_concepts,
                    'up': up_count,
                    'down': down_count,
                    'flat': flat_count
                }
        except Exception as e:
            print(f"Error getting concept data: {e}")
            concept_df = None
            
        return market_data, sector_df, concept_df
    except Exception as e:
        print(f"Error getting market overview: {e}")
        return {}, None, None