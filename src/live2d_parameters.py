import json
import os
from typing import Dict, List, Optional, Tuple
import logging

# 配置日志记录器
logger = logging.getLogger(__name__)

class Live2DParameters:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model_file = None
        self.expressions = []
        self.motions = []
        self.physics = []
        self.pose = []
        self.parameters = {}
        self.parts = []
        self.load_parameters()
        
    def load_parameters(self):
        """加载模型参数"""
        # 检查.model3.json文件
        model3_file = os.path.join(self.model_path, f"{os.path.basename(self.model_path)}.model3.json")
        if os.path.exists(model3_file):
            self.model_file = model3_file
            self._load_model3_parameters()
        else:
            # 检查.model.json文件
            model_file = os.path.join(self.model_path, f"{os.path.basename(self.model_path)}.model.json")
            if os.path.exists(model_file):
                self.model_file = model_file
                self._load_model_parameters()
                
        # 检查.vtube.json文件
        vtube_file = os.path.join(self.model_path, f"{os.path.basename(self.model_path)}.vtube.json")
        if os.path.exists(vtube_file):
            self._load_vtube_parameters(vtube_file)
            
        # 检查.cdi3.json文件
        cdi3_file = os.path.join(self.model_path, f"{os.path.basename(self.model_path)}.cdi3.json")
        if os.path.exists(cdi3_file):
            self._load_cdi3_parameters(cdi3_file)
            
        # 直接扫描.exp3.json文件
        self._scan_expressions()
            
    def _load_model3_parameters(self):
        """加载.model3.json文件参数"""
        try:
            with open(self.model_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 加载表情
            if 'FileReferences' in data and 'Expressions' in data['FileReferences']:
                for expr in data['FileReferences']['Expressions']:
                    self.expressions.append({
                        'name': os.path.splitext(os.path.basename(expr['Name']))[0],
                        'file': os.path.join(self.model_path, expr['File']),
                        'fade_in': expr.get('FadeInTime', 0.5),
                        'fade_out': expr.get('FadeOutTime', 0.5)
                    })
                    
            # 加载动作
            if 'FileReferences' in data and 'Motions' in data['FileReferences']:
                for group_name, motions in data['FileReferences']['Motions'].items():
                    for motion in motions:
                        self.motions.append({
                            'name': os.path.splitext(os.path.basename(motion['File']))[0],
                            'file': os.path.join(self.model_path, motion['File']),
                            'group': group_name,
                            'fade_in': motion.get('FadeInTime', 0.5),
                            'fade_out': motion.get('FadeOutTime', 0.5),
                            'sound': motion.get('Sound', None)
                        })
                        
            # 加载物理效果
            if 'FileReferences' in data and 'Physics' in data['FileReferences']:
                physics_file = data['FileReferences']['Physics']
                if physics_file:
                    physics_path = os.path.join(self.model_path, physics_file)
                    if os.path.exists(physics_path):
                        self.physics.append({
                            'name': os.path.splitext(os.path.basename(physics_file))[0],
                            'file': physics_path
                        })
                        logger.info(f"物理效果文件加载成功: {physics_path}")
                    else:
                        logger.warning(f"物理效果文件不存在: {physics_path}")
                        
            # 加载姿势
            if 'FileReferences' in data and 'Pose' in data['FileReferences']:
                pose_file = data['FileReferences']['Pose']
                if pose_file:
                    pose_path = os.path.join(self.model_path, pose_file)
                    if os.path.exists(pose_path):
                        self.pose.append({
                            'name': os.path.splitext(os.path.basename(pose_file))[0],
                            'file': pose_path
                        })
                        logger.info(f"姿势文件加载成功: {pose_path}")
                    else:
                        logger.warning(f"姿势文件不存在: {pose_path}")
                        
            # 加载参数
            if 'Groups' in data:
                for group in data['Groups']:
                    if group['Target'] == 'Parameter':
                        for param in group['Ids']:
                            self.parameters[param] = {
                                'min': 0.0,
                                'max': 1.0,
                                'default': 0.0
                            }
                        logger.info(f"参数组加载成功: {group['Name']}")
                            
            # 加载部件
            if 'Groups' in data:
                for group in data['Groups']:
                    if group['Target'] == 'Part':
                        for part in group['Ids']:
                            self.parts.append(part)
                        logger.info(f"部件组加载成功: {group['Name']}")
                            
        except Exception as e:
            logger.error(f"加载.model3.json参数失败: {e}")
            raise
            
    def _load_model_parameters(self):
        """加载.model.json文件参数"""
        try:
            with open(self.model_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 加载表情
            if 'expressions' in data:
                for expr in data['expressions']:
                    self.expressions.append({
                        'name': expr['name'],
                        'file': os.path.join(self.model_path, expr['file']),
                        'fade_in': expr.get('fade_in', 0.5),
                        'fade_out': expr.get('fade_out', 0.5)
                    })
                    
            # 加载动作
            if 'motions' in data:
                for group_name, motions in data['motions'].items():
                    for motion in motions:
                        self.motions.append({
                            'name': motion['name'],
                            'file': os.path.join(self.model_path, motion['file']),
                            'group': group_name,
                            'fade_in': motion.get('fade_in', 0.5),
                            'fade_out': motion.get('fade_out', 0.5),
                            'sound': motion.get('sound', None)
                        })
                        
            # 加载参数
            if 'parameters' in data:
                for param in data['parameters']:
                    self.parameters[param['id']] = {
                        'min': param.get('min', 0.0),
                        'max': param.get('max', 1.0),
                        'default': param.get('default', 0.0)
                    }
                    
            # 加载部件
            if 'parts' in data:
                for part in data['parts']:
                    self.parts.append(part['id'])
                    
        except Exception as e:
            logger.error(f"加载.model.json参数失败: {e}")
            
    def _load_vtube_parameters(self, vtube_file):
        """加载.vtube.json文件参数"""
        try:
            with open(vtube_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 加载表情
            if 'expressions' in data:
                for expr in data['expressions']:
                    # 构建表情文件路径
                    expr_file = os.path.join(self.model_path, f"{expr['name']}.exp3.json")
                    if os.path.exists(expr_file):
                        self.expressions.append({
                            'name': expr['name'],
                            'file': expr_file,
                            'fade_in': expr.get('fadeInTime', 0.5),
                            'fade_out': expr.get('fadeOutTime', 0.5)
                        })
                        logger.info(f"加载表情: {expr['name']}")
                    else:
                        logger.warning(f"表情文件不存在: {expr_file}")
                        
        except Exception as e:
            logger.error(f"加载.vtube.json参数失败: {e}")
            
    def _load_cdi3_parameters(self, cdi3_file):
        """加载.cdi3.json文件参数"""
        try:
            with open(cdi3_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 加载表情
            if 'expressions' in data:
                for expr in data['expressions']:
                    # 构建表情文件路径
                    expr_file = os.path.join(self.model_path, f"{expr['name']}.exp3.json")
                    if os.path.exists(expr_file):
                        self.expressions.append({
                            'name': expr['name'],
                            'file': expr_file,
                            'fade_in': expr.get('fadeInTime', 0.5),
                            'fade_out': expr.get('fadeOutTime', 0.5)
                        })
                        logger.info(f"加载表情: {expr['name']}")
                    else:
                        logger.warning(f"表情文件不存在: {expr_file}")
                        
        except Exception as e:
            logger.error(f"加载.cdi3.json参数失败: {e}")
            
    def _scan_expressions(self):
        """扫描.exp3.json文件"""
        try:
            # 遍历模型目录下的所有文件
            for file in os.listdir(self.model_path):
                if file.endswith('.exp3.json'):
                    # 获取表情名称（去掉.exp3.json后缀）
                    expr_name = os.path.splitext(os.path.splitext(file)[0])[0]
                    expr_file = os.path.join(self.model_path, file)
                    
                    # 读取表情文件内容
                    with open(expr_file, 'r', encoding='utf-8') as f:
                        expr_data = json.load(f)
                        
                    # 检查是否是有效的表情文件
                    if expr_data.get('Type') == 'Live2D Expression':
                        self.expressions.append({
                            'name': expr_name,
                            'file': expr_file,
                            'fade_in': 0.5,
                            'fade_out': 0.5
                        })
                        logger.info(f"加载表情: {expr_name}")
                    else:
                        logger.warning(f"无效的表情文件格式: {expr_file}")
                        
        except Exception as e:
            logger.error(f"扫描表情文件失败: {e}")
            
    def get_expressions(self) -> List[Dict]:
        """获取表情列表"""
        return self.expressions
        
    def get_motions(self) -> List[Dict]:
        """获取动作列表"""
        return self.motions
        
    def get_physics(self) -> List[Dict]:
        """获取物理效果列表"""
        return self.physics
        
    def get_pose(self) -> List[Dict]:
        """获取姿势列表"""
        return self.pose
        
    def get_parameters(self) -> Dict:
        """获取参数列表"""
        return self.parameters
        
    def get_parts(self) -> List[str]:
        """获取部件列表"""
        return self.parts
        
    def get_expression(self, name: str) -> Optional[Dict]:
        """获取指定名称的表情"""
        for expr in self.expressions:
            if expr['name'] == name:
                return expr
        return None
        
    def get_motion(self, name: str) -> Optional[Dict]:
        """获取指定名称的动作"""
        for motion in self.motions:
            if motion['name'] == name:
                return motion
        return None
        
    def get_physics_by_name(self, name: str) -> Optional[Dict]:
        """获取指定名称的物理效果"""
        for physics in self.physics:
            if physics['name'] == name:
                return physics
        return None
        
    def get_pose_by_name(self, name: str) -> Optional[Dict]:
        """获取指定名称的姿势"""
        for pose in self.pose:
            if pose['name'] == name:
                return pose
        return None
        
    def get_parameter_range(self, name: str) -> Optional[Tuple[float, float]]:
        """获取指定参数的取值范围"""
        if name in self.parameters:
            param = self.parameters[name]
            return (param['min'], param['max'])
        return None
        
    def get_parameter_default(self, name: str) -> Optional[float]:
        """获取指定参数的默认值"""
        if name in self.parameters:
            return self.parameters[name]['default']
        return None 