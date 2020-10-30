from flask import Blueprint,render_template, request, g, redirect, url_for
from .auth import login_required
from . import db
from webdocs.dmvhaninlib.filestream import upload_request_file_to_s3

bp = Blueprint('car', __name__, url_prefix='/car')


def get_main_img(x):
    imgs = x.split(';');
    for img in imgs:
        if img:
            return img
    return ''


@bp.route('/', methods=('GET',))
def index():
    cars = db.select_rows(
        "SELECT * FROM car a "\
        "INNER JOIN dealer b "\
        "ON a.dealer_id = b.dealer_id "\
        "WHERE a.active_flag = TRUE AND b.active_flag = TRUE "\
        "ORDER BY on_sale DESC, car_id"
    )
    if cars.empty:
        cars = None
    else:
        cars['image'] = cars['image'].apply(get_main_img)
        cars['price'] = cars['price'].apply(int)
        cars = cars.to_dict('index')
        
    return render_template('car/index.html', cars = cars)


@bp.route('/mylist', methods=('GET', ))
@login_required
def mylist():
    if not g.user['dealer_id']:
        return redirect(url_for('car.index'))
    cars = db.select_rows(
        "SELECT * FROM car "\
        "WHERE dealer_id = %s AND active_flag = TRUE "\
        "ORDER BY on_sale DESC, car_id", [g.user['dealer_id']]
    )
    
    if cars.empty:
        cars = None
    else:
        cars['image'] = cars['image'].apply(get_main_img)
        cars['price'] = cars['price'].apply(int)
        cars = cars.to_dict('records')
    
    return render_template('car/listview.html', cars = cars)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if not g.user['dealer_id']:
        return redirect(url_for('car.index'))
    if request.method == 'POST':
        title = request.form['title']
        transmission = request.form['transmission']
        fuel = request.form['fuel']
        car_type = request.form['car_type']
        manufacturer = request.form['manufacturer']
        model = request.form['model']
        seat = request.form['seat']
        color = request.form['color']
        sale_type = request.form['sale_type']
        used = request.form['used']
        vin = request.form['vin']
        mileage = request.form['mileage']
        year = request.form['year']
        displacement = request.form['displacement']
        accident = request.form['accident']
        price = request.form['price']
        description = request.form['description']
        files = ['' for _ in range(8)]
        for i in range(8):
            file = request.files['file'+str(i+1)]
            if file:
                url = upload_request_file_to_s3(file, folder="car")
            else:
                url = ''
            files[i] = url
        files = ';'.join(files)
        print(g.user['dealer_id'], title, description, files, manufacturer, model, used, mileage, year, car_type, displacement, seat, vin, 
            color, fuel, transmission, price, accident, sale_type)
        db.update_rows(
            "INSERT INTO car (dealer_id, title, description, image, manufacturer, model, used, mileage, year, car_type, displacement, seat, vin, "\
            "                 color, fuel, transmission, price, accident, sale_type) "\
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ",
            [g.user['dealer_id'], title, description, files, manufacturer, model, used, mileage, year, car_type, displacement, seat, vin, 
            color, fuel, transmission, price, accident, sale_type]
        )
        car_id = db.select_row(
           "SELECT LASTVAL()"
        )['lastval']
        return redirect(url_for('car.detail', car_id = car_id))
    return render_template('car/create.html')
    
@bp.route('/detail/<int:car_id>', methods=('GET',))
def detail(car_id):
    car = db.select_row(
        "SELECT * FROM car a "\
        "INNER JOIN dealer b "\
        "ON a.dealer_id = b.dealer_id "\
        "WHERE a.car_id = %s "\
        "AND a.active_flag = TRUE "\
        "AND b.active_flag = TRUE",[car_id]
    )
    
    if not car:
        return redirect(url_for('car.index'))
    
    car['mileage'] = int(car['mileage'])
    car['year'] = int(car['year'])
    car['displacement'] = int(car['displacement'])
    car['seat'] = int(car['seat'])
    car['price'] = int(car['price'])
    car['accident'] = int(car['accident'])
    car['image'] = car['image'].split(';')
    
    return render_template('car/detail.html', car=car)
    
@bp.route('/modify/<int:car_id>', methods=('GET','POST'))
@login_required
def modify(car_id):
    car = db.select_row(
        "SELECT * FROM car WHERE car_id = %s AND active_flag = TRUE", [car_id]
    )
    if not car or car['dealer_id'] != g.user['dealer_id']:
        return redirect(url_for('car.index'))
    
    if request.method == 'POST':
        title = request.form['title']
        transmission = request.form['transmission']
        fuel = request.form['fuel']
        car_type = request.form['car_type']
        manufacturer = request.form['manufacturer']
        model = request.form['model']
        seat = request.form['seat']
        color = request.form['color']
        sale_type = request.form['sale_type']
        used = request.form['used']
        vin = request.form['vin']
        mileage = request.form['mileage']
        year = request.form['year']
        displacement = request.form['displacement']
        accident = request.form['accident']
        price = request.form['price']
        description = request.form['description']
        files = ['' for _ in range(8)]
        images = car['image'].split(';')
        for i in range(8):
            file = request.files['file'+str(i+1)]
            if file:
                url = upload_request_file_to_s3(file, folder="car")
                files[i] = url
            else:
                files[i] = images[i]
        files = ';'.join(files)
        db.update_rows(
            "UPDATE car SET title=%s, description=%s, image=%s, manufacturer=%s, model=%s, used=%s, mileage=%s, year=%s, car_type=%s, "\
            "               displacement=%s, seat=%s, vin=%s, color=%s, "\
            "               fuel=%s, transmission=%s, price=%s, accident=%s, sale_type=%s "\
            "WHERE car_id = %s ",
            [title, description, files, manufacturer, model, used, mileage, year, car_type, displacement, seat, vin, color,
            fuel, transmission, price, accident, sale_type, car_id]
        )

        return redirect(url_for('car.detail', car_id = car_id))
    
    car['mileage'] = int(car['mileage'])
    car['year'] = int(car['year'])
    car['displacement'] = int(car['displacement'])
    car['seat'] = int(car['seat'])
    car['price'] = int(car['price'])
    car['accident'] = int(car['accident'])
    car['image'] = enumerate(car['image'].split(';'))
    
    return render_template('car/create.html', car=car)
    
@bp.route('/complete/<int:car_id>', methods=('GET',))
def complete(car_id):
    car = db.select_row(
        "SELECT * FROM car WHERE car_id = %s AND active_flag = TRUE", [car_id]
    )
    if car and (car['dealer_id'] == g.user['dealer_id']):
        db.update_rows(
            "UPDATE car SET on_sale= NOT on_sale WHERE car_id = %s", [car_id]
        )
    
    return redirect(url_for('car.detail', car_id = car_id))    
        
@bp.route('/delete/<int:car_id>', methods=('GET',))
def delete(car_id):
    car = db.select_row(
        "SELECT * FROM car WHERE car_id = %s AND active_flag = TRUE", [car_id]
    )
    if car and (car['dealer_id'] == g.user['dealer_id'] or g.user['admin_flag']):
        db.update_rows(
            "UPDATE car SET active_flag=FALSE WHERE car_id = %s", [car_id]
        )
    
    return redirect(url_for('car.index'))