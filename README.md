# flask_login_multi
> Flask-Login with multiple models: User Model,Admin Model ...  only for python3.6



##### 1.setup  Flask_Login  
##### 2.import flask_login_multi  
```
from flask import Flask
from flask_login_multi.login_manager import LoginManager   

app=Flask(__name__)

login_manager = LoginManager(app)   

login_manager.blueprint_login_views = {  
        'user':  "user.user_login",  
        'admin': "admin.admin_login",  
    }  
```
  

##### 3.set buleprint  
```
admin_app = Blueprint('admin', __name__, url_prefix="/admin")  
user_app = Blueprint('user', __name__, url_prefix="/user")  
```

  
##### 4. model add user_loader  
```
@login_manager.user_loader
def load_user(id, endpoint='user'):
    if endpoint == 'admin':
        return Admin.query.get(id)
    else:
        return User.query.get(id)
```
        
 ##### 5. admin or user login   
```
 from app.libs.flask_login_multi import login_user
 #user
 user = User.query.filter_by(name=form.name.data).first()
 login_user(user,remember=True)
 #admin
 user = Admin.query.filter_by(name=form.name.data).first()
 login_user(admin)
 ```
 
 ##### 6.admin login required  
 ```
 from app.libs.flask_login_multi import login_required,current_user  
   
@admin_app.route('/index')  
@login_required  
def index():  
    print(current_user)  
    return 'admin.index'  
 ```
 
 
###  flask login 本身支持多表登录，所以本库不再维护

#### 模型表 admin
```
 # get_id 返回str字符串，通过 admin 来做标识
    def get_id(self):
        return 'admin.' + str(self.id)
```

#### 模型表 user
```
 # get_id 返回str字符串，通过 user 来做标识
    def get_id(self):
        return 'user.' + str(self.id)
```

#### 验证登录
```
@login_manager.user_loader
def load_user(user_id):
    temp = user_id.split('.')
    try:
        uid = temp[1]
        if temp[0] == 'admin':
            return Admin.query.get(uid)
        elif temp[0] == 'user':
            return User.query.get(uid)
        else:
            return None
    except IndexError:
        return None
```


详情 加qq群：184596631
