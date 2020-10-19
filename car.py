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
        "WHERE active_flag = TRUE AND dealer_id = %s "\
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
        address = request.form['address']
        city = request.form['city']
        state = request.form['state']
        zipcode = request.form['zipcode']
        sale_type = request.form['sale_type']
        house_type = request.form['house_type']
        num_room = request.form['num_room']
        num_rest = request.form['num_rest']
        price = request.form['price']
        year = request.form['year']
        size = request.form['size']
        description = request.form['description']
        files = ['' for _ in range(8)]
        for i in range(8):
            file = request.files['file'+str(i+1)]
            if file:
                url = upload_request_file_to_s3(file)
            else:
                url = ''
            files[i] = url
        files = ';'.join(files)
        db.update_rows(
            "INSERT INTO estate (realtor_id, title, description, image, address, city, state, zipcode, "\
            "   house_type, num_room, num_rest, year, sale_type, price, size) "\
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ",
            [g.user['realtor_id'], title, description, files, address, city, state, zipcode, house_type, num_room, num_rest, year, sale_type, price, size]
        )
        estate_id = db.select_row(
           "SELECT LASTVAL()"
        )['lastval']
        return redirect(url_for('estate.detail', estate_id = estate_id))
    return render_template('estate/create.html')
    
@bp.route('/detail/<int:car_id>', methods=('GET',))
def detail(car_id):
    car = db.select_row(
        "SELECT * FROM car a "\
        "LEFT JOIN dealer b "\
        "ON a.dealer_id = b.dealer_id "\
        "WHERE a.active_flag = TRUE AND a.dealer_id = %s",[car_id]
    )
    
    if not car:
        return redirect(url_for('car.index'))
    
    estate['num_room'] = int(estate['num_room'])
    estate['size'] = int(estate['size'])
    estate['price'] = int(estate['price'])
    estate['num_rest'] = int(estate['num_rest']) if estate['num_rest'] == int(estate['num_rest']) else estate['num_rest']
    if estate['image']:
        estate['image'] = estate['image'].split(';')
    
    return render_template('estate/detail.html', estate=estate)
    
@bp.route('/modify/<int:estate_id>', methods=('GET','POST'))
@login_required
def modify(estate_id):
    estate = db.select_row(
        "SELECT * FROM estate WHERE active_flag = TRUE AND estate_id = %s", [estate_id]
    )
    if not estate or estate['realtor_id'] != g.user['realtor_id']:
        return redirect(url_for('estate.index'))
    
    if request.method == 'POST':
        title = request.form['title']
        address = request.form['address']
        city = request.form['city']
        state = request.form['state']
        zipcode = request.form['zipcode']
        sale_type = request.form['sale_type']
        house_type = request.form['house_type']
        num_room = request.form['num_room']
        num_rest = request.form['num_rest']
        price = request.form['price']
        year = request.form['year']
        size = request.form['size']
        description = request.form['description']
        files = ['' for _ in range(8)]
        images = estate['image'].split(';')
        for i in range(8):
            file = request.files['file'+str(i+1)]
            if file:
                url = upload_request_file_to_s3(file)
                files[i] = url
            else:
                files[i] = images[i]
        files = ';'.join(files)
        db.update_rows(
            "UPDATE estate SET title=%s, description=%s, image=%s, address=%s, city=%s, state=%s, zipcode=%s, "\
            "                  house_type=%s, num_room=%s, num_rest=%s, year=%s, sale_type=%s, price=%s, size=%s "\
            "WHERE estate_id = %s ",
            [title, description, files, address, city, state, zipcode, house_type, num_room, num_rest, year, sale_type, price, size, estate_id]
        )

        return redirect(url_for('car.detail', estate_id = estate_id))
    
    estate['num_room'] = int(estate['num_room'])
    estate['size'] = int(estate['size'])
    estate['price'] = int(estate['price'])
    estate['num_rest'] = int(estate['num_rest']) if estate['num_rest'] == int(estate['num_rest']) else estate['num_rest']
    estate['image'] = enumerate(estate['image'].split(';'))
    
    return render_template('car/create.html', estate=estate)
    
@bp.route('/complete/<int:car_id>', methods=('GET',))
def complete(car_id):
    car = db.select_row(
        "SELECT * FROM car WHERE active_flag = TRUE AND car_id = %s", [car_id]
    )
    if car and (car['dealer_id'] == g.user['dealer_id']):
        db.update_rows(
            "UPDATE car SET on_sale= NOT on_sale WHERE car_id = %s", [car_id]
        )
    
    return redirect(url_for('car.detail', car_id = car_id))    
        
@bp.route('/delete/<int:car_id>', methods=('GET',))
def delete(car_id):
    car = db.select_row(
        "SELECT * FROM car WHERE active_flag = TRUE AND car_id = %s", [car_id]
    )
    if car and (car['dealer_id'] == g.user['dealer_id'] or g.user['admin_flag']):
        db.update_rows(
            "UPDATE car SET active_flag=FALSE WHERE car_id = %s", [car_id]
        )
    
    return redirect(url_for('car.index'))