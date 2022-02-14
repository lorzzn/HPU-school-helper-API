
import pymysql, time

# 208 - Fine


# 打开数据库连接
db = pymysql.connect(host="localhost",user="hpu_xyzs_system",password="NY7W75JpjdGt4yAD",database="hpu_xyzs_system")
 
# 使用cursor()方法获取操作游标 
cursor = db.cursor()

def update_session(content):
    # sql删除
    delete_sql = """
    DELETE FROM eams_session WHERE id = '208' 
    """
    # SQL 更新
    sql = f"""
    INSERT INTO eams_session(user_id, content,  create_time) 
    VALUES("208", "{content}", "{int(time.time())}")
    """
    try:
        # 执行sql语句
        cursor.execute(delete_sql)
        cursor.execute(sql)
        # 提交到数据库执行
        db.commit()
        return True
    except:
         # 如果发生错误则回滚
         db.rollback()
         return False