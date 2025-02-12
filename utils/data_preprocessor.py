import akshare as ak
import pandas as pd
import json
from datetime import datetime
import os
import time
from tqdm import tqdm

def get_data_with_retry(func, symbol, max_retries=3, retry_delay=2):
    """带重试机制的数据获取函数"""
    for attempt in range(max_retries):
        try:
            return func(symbol=symbol)
        except Exception as e:
            if attempt == max_retries - 1:  # 最后一次尝试
                raise e
            print(f"获取数据失败，{retry_delay}秒后重试: {str(e)}")
            time.sleep(retry_delay)
            continue

def preprocess_sector_data(test_mode=True):
    """
    预处理板块数据，将数据保存为易于查询的格式
    test_mode: 如果为True，只处理少量数据进行测试
    """
    start_time = time.time()
    
    # 创建数据目录
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # 初始化数据结构 - 只存储股票到板块的映射
    stock_sectors = {}  # 股票所属板块信息
    metadata = {
        'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'test_mode': test_mode,
        'total_industries': 0,
        'total_concepts': 0,
        'processing_time': 0
    }
    
    try:
        # 处理行业板块
        print("\n开始获取行业板块列表...")
        industry_list = ak.stock_board_industry_name_em()
        
        # 测试模式下只处理前3个行业
        if test_mode:
            industry_list = industry_list.head(3)
        
        total_industries = len(industry_list)
        metadata['total_industries'] = total_industries
        print(f"共找到 {total_industries} 个行业板块")
        
        # 使用tqdm创建进度条
        for idx, (_, industry) in enumerate(tqdm(industry_list.iterrows(), total=total_industries, desc="处理行业板块")):
            industry_name = industry['板块名称']
            
            try:
                # 获取行业成分股（带重试机制）
                stocks = get_data_with_retry(ak.stock_board_industry_cons_em, industry_name)
                
                # 更新股票所属板块信息
                for _, stock in stocks.iterrows():
                    code = stock['代码']
                    if code not in stock_sectors:
                        stock_sectors[code] = {
                            'name': stock['名称'],
                            'industry': [],
                            'concept': []
                        }
                    if industry_name not in stock_sectors[code]['industry']:
                        stock_sectors[code]['industry'].append(industry_name)
                
            except Exception as e:
                print(f"\n处理行业 {industry_name} 时出错: {str(e)}")
                continue
        
        # 处理概念板块
        print("\n开始获取概念板块列表...")
        concept_list = ak.stock_board_concept_name_em()
        
        # 测试模式下只处理前5个概念
        if test_mode:
            concept_list = concept_list.head(5)
            
        total_concepts = len(concept_list)
        metadata['total_concepts'] = total_concepts
        print(f"共找到 {total_concepts} 个概念板块")
        
        # 使用tqdm创建进度条
        for idx, (_, concept) in enumerate(tqdm(concept_list.iterrows(), total=total_concepts, desc="处理概念板块")):
            concept_name = concept['板块名称']
            
            try:
                # 获取概念成分股（带重试机制）
                stocks = get_data_with_retry(ak.stock_board_concept_cons_em, concept_name)
                
                # 更新股票所属板块信息
                for _, stock in stocks.iterrows():
                    code = stock['代码']
                    if code not in stock_sectors:
                        stock_sectors[code] = {
                            'name': stock['名称'],
                            'industry': [],
                            'concept': []
                        }
                    if concept_name not in stock_sectors[code]['concept']:
                        stock_sectors[code]['concept'].append(concept_name)
                
            except Exception as e:
                print(f"\n处理概念 {concept_name} 时出错: {str(e)}")
                continue
        
        # 计算处理时间
        processing_time = time.time() - start_time
        metadata['processing_time'] = f"{processing_time:.2f}秒"
        
        # 保存数据到文件
        data = {
            'metadata': metadata,
            'stocks': stock_sectors
        }
        
        filename = 'sector_data_test.json' if test_mode else 'sector_data.json'
        filepath = os.path.join(data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n数据处理完成，已保存到 {filepath}")
        print(f"处理了 {metadata['total_industries']} 个行业和 {metadata['total_concepts']} 个概念")
        print(f"共收集了 {len(stock_sectors)} 只股票的板块信息")
        print(f"处理用时: {metadata['processing_time']}")
        
        # 显示数据大小
        file_size = os.path.getsize(filepath) / 1024  # KB
        print(f"数据文件大小: {file_size:.2f} KB")
        
        return data
        
    except Exception as e:
        print(f"数据预处理失败: {str(e)}")
        return None

def load_sector_data(test_mode=True):
    """加载预处理的板块数据"""
    filename = 'sector_data_test.json' if test_mode else 'sector_data.json'
    filepath = os.path.join('data', filename)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data['stocks']  # 只返回股票数据部分
    except Exception as e:
        print(f"加载数据失败: {str(e)}")
        return None

if __name__ == "__main__":
    # 运行测试模式
    print("运行测试模式，只处理少量数据...")
    data = preprocess_sector_data(test_mode=True)
    
    if data:
        # 测试数据查询
        print("\n测试数据查询:")
        # 随机选择一个股票进行测试
        test_stock = list(data['stocks'].keys())[0]
        print(f"\n股票 {test_stock} 的板块信息:")
        print(json.dumps(data['stocks'][test_stock], ensure_ascii=False, indent=2)) 