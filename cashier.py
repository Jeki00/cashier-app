from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymongo, bcrypt
from datetime import date,datetime
from functools import wraps
from bson.objectid import ObjectId

myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
mydb = myclient["cashier"]

userCol = mydb['users']
menuCol = mydb['menus']
orderCol = mydb['orders']


app = Flask(__name__)
app.secret_key = 'secret'

def auth_user(user):
    session['loggedIn'] = True
    session['username'] = user['username']
    session['role'] = user['role']

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'loggedIn' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first')
            return redirect(url_for('login'))
    return wrap



@app.route("/",methods=['GET','POST'])
@login_required
def home():
    if request.method == 'POST':
        total = 0
        menus = menuCol.find({}, {'_id':0,'menu':1, 'harga':1})
        # qty = request.form['qty_tahu']
        # print(qty)
        mydict = {
            'nama': request.form['nama'],
            'pelayan': session['username'],
            'date': datetime.now(),
            'orders':[]
        }
    
        for menu in menus:
            qty = request.form[f"qty_{menu['menu']}"]
            if qty == '':
                continue
            mydict['orders'].append( {
                'menu':menu['menu'],
                'harga':menu['harga'],
                'jumlah':int(qty),
                'subtotal':int(qty)*menu['harga']
            })

            total += int(qty)*menu['harga']
        
        mydict['total'] = total

        orderCol.insert_one(mydict)
        flash('berhasil menambahkan order')
        return redirect(url_for('home'))


    makanan = menuCol.find({'kategori':'makanan'},{'_id':0, 'menu':1, 'harga':1,'kategori':1 })
    minuman = menuCol.find({'kategori':'minuman'},{'_id':0, 'menu':1, 'harga':1,'kategori':1 })
    lainnya = menuCol.find({'kategori':'lain-lainnya'},{'_id':0, 'menu':1, 'harga':1,'kategori':1 })
    return render_template('home.html', makanan=makanan,minuman=minuman,lainnya=lainnya )


@app.route("/users", methods=['GET','POST'])
@login_required
def register():
    if request.method == 'POST':
        mydict = {
            'username': request.form['username'],
            'password': bcrypt.hashpw(request.form['password'].encode("utf-8"), bcrypt.gensalt(14)),
            'role':'pegawai'
        }

        x = userCol.insert_one(mydict)

        newUser = userCol.find_one({'_id':x.inserted_id})
        return redirect(url_for('register'))


    users = userCol.find()
    return render_template('user.html',users=users)
@app.route("/users/<user_id>", methods=['GET'])
@login_required
def delete_user(user_id):
    userCol.delete_one({'_id':ObjectId(user_id)})
    return redirect(url_for('register'))


@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == 'POST':
        foundUser = userCol.find_one({
            'username': request.form['username']
        })

        if bcrypt.checkpw(request.form['password'].encode("utf-8"), foundUser['password']):
            auth_user(foundUser)

            # print(foundUser)
            return redirect(url_for('home'))
        else:
            flash('username dan password salah')
            return redirect(url_for('login'))


    return render_template('login.html')

@app.route("/menu", methods=['GET','POST'])
@login_required
def menu():
    if request.method == 'POST':
        
        mydict = {
            'menu': request.form['menu'],
            'harga': int(request.form['harga']),
            'kategori': request.form['kategori'],
        }
        menuCol.insert_one(mydict)
        flash('menu berhasil ditambahkan')
        return redirect(url_for('menu'))
    # check_auth()
    menus = menuCol.find()
    
    return render_template('menu.html', menus=menus)

@app.route("/menu/<menu_id>", methods=['POST'])
@login_required
def editmenu(menu_id):
    menuCol.update_one(
        {'_id': ObjectId(menu_id)}, 
        {'$set':{
            'menu':request.form['menu'],
            'harga':int(request.form['harga']),
            'kategori':request.form['kategori']
            }
        }
        )

    flash('menu berhasil diedit')
    # print(menu_id)
    # print(menuCol.find_one({'_id':ObjectId(menu_id)}))

    return redirect(url_for('menu'))

@app.route("/menu/<menu_id>/delete", methods=['GET'])
@login_required
def delete(menu_id):
    menuCol.delete_one({'_id': ObjectId(menu_id)})

    # print(menu_id)
    # print(menuCol.find_one({'_id':ObjectId(menu_id)}))

    return redirect(url_for('menu'))


@app.route("/order",methods=['GET','POST'])
@login_required
def order():
    fromDate = request.args.get('from')
    toDate = request.args.get('to')
    myQuery = {}
    if fromDate or toDate:
        myQuery['date']= {'$lte':toDate,'$gte':fromDate}
    orders = orderCol.find(myQuery,{'_id':0}).sort('date',pymongo.DESCENDING)


    return render_template('orders.html', orders = orders)

@app.route("/order/<order_id>",methods=['GET','POST'])
@login_required
def show_order(order_id):
    myQuery = {'_id': ObjectId(order_id)}
    order = orderCol.find(myQuery)


    return render_template('order.html', order = order)


@app.route("/logout")
@login_required
def logout():
    session.pop('username', None)
    session.pop('loggedIn', None)

    return redirect(url_for('login'))


if __name__ == '__main__':  
    app.run(debug = True)




