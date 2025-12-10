from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file
from . import db
from .models import User, Product, Category, Stock, Location, Sale, SaleDetail, LogMesssage, UserLoginLog
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import joinedload
from sqlalchemy import func, extract, select, desc, asc
from datetime import datetime, timedelta
import csv
from io import StringIO, BytesIO




views = Blueprint("views", __name__)





# Home screen

@views.route("/")
@views.route("/home")
def home():
    
    return render_template("home.html", user = current_user)





# To Admin Panel

@views.route("/admin_panel")
@login_required
def admin_panel():

    stocks = Stock.query.all()
    logMesssages = LogMesssage.query.all()

    low_stock = 0
    notifi_count = 0

    for stock in stocks:
        if stock.quantity < 10:
            flash(f'{stock.stock_name}\'s current stock is low...', category='warning')
            low_stock += 1
            # return low_stock


    for logMesssage in logMesssages:
        notifi_count += 1


    return render_template("admin_panel.html",low_stock=low_stock , username = current_user.username, user = current_user, notifi_count = notifi_count)








# See Product and Category list

@views.route("/see_list")
@login_required
def see_list():
    # items = Product.query.all()
    categories = Category.query.all()

    # item_cat = Category.products

    items = db.session.query(Product).options(joinedload(Product.stocks)).all()

    locations = Location.query.all()




    return render_template("see_list.html",locations = locations, user = current_user, items = items, categories = categories)











# See the Stock 

@views.route("/see_stocks")
@login_required
def see_stocks():

    product = Product.query.all()
    stocks = db.session.query(Stock).options(joinedload(Stock.product)).all()

    sort_by = request.args.get('sort', 'id')
    direction = request.args.get('direction', 'asc')

    if sort_by == 'quantity':
        column = Stock.quantity
    elif sort_by == 'ProductType':
        column = Stock.product_id
    elif sort_by == 'name':
        column = Stock.stock_name
    else:
        # Default sort column
        column = Stock.id

    if direction == 'desc':
        stocks = Stock.query.order_by(desc(column)).all()
    else:
        # Default to ascending
        stocks = Stock.query.order_by(asc(column)).all()


    
    

    return render_template("see_stock.html",stocks=stocks, user=current_user, current_sort=sort_by, current_direction=direction)




@views.route("/see_sales")
@login_required
def see_sales():
    """
    Fetches comprehensive sales data by joining Sale, SaleDetail, and Stock tables.
    The query calculates the line-item total (quantity * selling_price)
    and produces a flat list of sales records suitable for the report table.
    """
    try:
        sales_data = db.session.query(
            Sale.sale_name,                                              
            Sale.buyer_name,                                             
            Sale.date_created,                                           
            Stock.stock_name.label('product_type'),                      
            SaleDetail.quantity_sold.label('quantity'),
            (SaleDetail.quantity_sold * Stock.selling_price).label('line_total_amount')
        ).join(SaleDetail, Sale.id == SaleDetail.sale_id
        ).join(Stock, SaleDetail.stock_id == Stock.id
        ).all() 

        
        report_items = []
        for row in sales_data:
            
            date_str = row.date_created.strftime('%Y-%m-%d %H:%M') if row.date_created else 'N/A'
            
            
            report_items.append({
                'sale_name': row.sale_name,
                'buyer_name': row.buyer_name,
                'date': date_str, 
                'product_type': row.product_type,
                'quantity': row.quantity,
               
                'total_amount': f"{row.line_total_amount:,.2f}" 
            })

        
        return render_template("see_sales.html", report_items=report_items, user = current_user)

    except Exception as e:
       
        print(f"Error generating sales report: {e}")
        flash_and_log("Could not load sales report due to an error.", "error")
        return render_template("see_sales.html", report_items=[]), 500






# Check the inventory

@views.route("/see_inventory")
@login_required
def see_inventory():

    stocks =db.session.query(Stock).options(joinedload(Stock.location)).all()
    stocks =db.session.query(Stock).options(joinedload(Stock.user)).all()

    products = Product.query.all()

    locations = Location.query.all()

    saleDetails = SaleDetail.query.all()

    saleDetail = db.session.query(SaleDetail).options(joinedload(SaleDetail.stock)).all()

    sort_by = request.args.get('sort', 'id')
    direction = request.args.get('direction', 'asc')

    if sort_by == 'quantity':
        column = Stock.quantity
    elif sort_by == 'salequantity':
        column = Stock.saled_quantity
    elif sort_by == 'location':
        column = Stock.location_id
    elif sort_by == 'name':
        column = Stock.stock_name
    else:
        # Default sort column
        column = Stock.id

    if direction == 'desc':
        stocks = Stock.query.order_by(desc(column)).all()
    else:
        # Default to ascending
        stocks = Stock.query.order_by(asc(column)).all()

    

    return render_template("inventory.html",saleDetails = saleDetails, saleDetail=saleDetail, products=products , stocks=stocks, locations = locations, user=current_user, current_sort=sort_by, current_direction=direction)











# Add Categories to invetory

@views.route("/add_categories", methods = ['GET','POST'])
@login_required
def add_categories():
    if request.method == 'POST':
        name = request.form.get('category_name')

        name_exists = Category.query.filter_by(category_name = name).first()

        if name_exists:
            flash_and_log("Category is already there...", category='error')
            return redirect(url_for('views.see_list'))
        
        else:

            new_category = Category(
                category_name = name,
                user_id = current_user.id
            )

            db.session.add(new_category)
            db.session.commit()
            flash_and_log(f'Categoty "{name}" added successfully!', category='success')
            return redirect(url_for('views.see_list'))
        
    return render_template('add_categories.html', user = current_user)










# Add Products to invetory

@views.route("/add_products", methods = ['GET', 'POST'])
@login_required
def add_products():

    categories = Category.query.all()

    if request.method == 'POST':
        name = request.form.get('item_name')
        category_id = request.form.get('category_id')

        if not name or not category_id:
            flash_and_log('All fields are required.',category='error')

        name_exists = Product.query.filter_by(item_name = name).first()

        if name_exists:
            flash_and_log("Product is already there...", category='error')
            return redirect(url_for('views.see_list'))
        

        else:
            try:
                category_id_int = int(category_id)

                selected_category = Category.query.get(category_id_int)

                if selected_category:
                    new_product = Product(
                        item_name = name,
                        category_id = category_id_int,
                        user_id = current_user.id
                    )

                    db.session.add(new_product)
                    db.session.commit()
                    flash_and_log(f'Product "{name}" added successfully!', category='success')
                    return redirect(url_for('views.see_list'))

                else:
                    flash_and_log('Invalid category selected.', category='error')

            except ValueError:
                flash_and_log('Invalid data format for price or category.', category='error')
                return redirect(url_for('views.see_list'))
    
    return render_template('add_products.html', user = current_user.id, categories = categories )






#Add Locations to inventory

@views.route("/add_locations", methods = ['GET', 'POST'])
@login_required
def add_locations():
    locations = Location.query.all()

    if request.method == 'POST':
        location_name = request.form.get('location_name')


        if not location_name:
            flash_and_log('All fields are required.',category='error')
        
        name_exists = Location.query.filter_by(location_name = location_name).first()

        if name_exists:
            flash_and_log("Location is already there...", category='error')
            return redirect(url_for('views.see_list'))
        
        else:
            new_location = Location(
                location_name = location_name,
                user_id = current_user.id
            )

            db.session.add(new_location)
            db.session.commit()
            flash_and_log(f'Location "{location_name}" added successfully!', category='success')
            return redirect(url_for('views.see_list'))
    
    return render_template('add_location.html', locations = locations, user = current_user)





# Add Stocks to invetory

@views.route("/add_stock", methods = ['GET', 'POST'])
@login_required
def add_stock():

    products = Product.query.all()
    categories = Category.query.all()
    locations = Location.query.all()
    
    

    if request.method == 'POST':
        name = request.form.get('stock_name')
        u_price = request.form.get('unit_price')
        s_price = request.form.get('selling_price')
        quant = request.form.get('quantity')
        product_id = request.form.get('product_id')
        location_id = request.form.get('location_id')
        description = request.form.get('description')

        u_price_float = float(u_price)
        s_price_float = float(s_price)
        
        
        

        if not name or not u_price or not s_price or not quant or not product_id or not description or not location_id:
            flash_and_log('All fields are required.',category='error')

        name_exists = Stock.query.filter_by(stock_name = name).first()

        if name_exists:
            flash_and_log("Product is already there...", category='error')
            return redirect(url_for('views.see_stocks'))
        
        
        
        elif u_price_float > s_price_float:
            flash_and_log("Product sellig price must be higher than unit price...", category='error')
            return redirect(url_for('views.see_stocks'))
        
        else:
            try:
                product_id_int = int(product_id)
                location_id_int = int(location_id)

                

                

                selected_product = Product.query.get(product_id_int)

                if selected_product:
                    new_stock = Stock(
                        stock_name = name,
                        unit_price = u_price,
                        selling_price = s_price,
                        quantity = quant,
                        stock_description = description,
                        product_id = product_id_int,
                        category_id = selected_product.category_id,
                        location_id = location_id_int, 
                        user_id = current_user.id
                    )

                    db.session.add(new_stock)
                    db.session.commit()
                    flash_and_log(f'Stock "{name}" added successfully!', category='success')
                    return redirect(url_for('views.see_stocks'))
                

                else:
                    flash_and_log('Invalid product selected.', category='error')

            except ValueError:
                flash_and_log('Invalid data format for price or product.', category='error')
                return redirect(url_for('views.see_stocks'))
            

    
                
    return render_template('add_stock.html', user = current_user.id, categories = categories, products = products, locations = locations )









# Update an existing Product

@views.route("/update_item/<id>", methods = ['GET', 'POST'])
@login_required
def update_item(id):

    stocks = Stock.query.all()
    stock = db.session.get(Stock, id)

    products = Product.query.all()
    product = db.session.get(Product, id)

    categories = Category.query.all()
    category = db.session.get(Category, id)

    
    if not product:
        flash_and_log('Product does not exist!...', category='error')

    if request.method == 'POST':
        new_product_name = request.form.get('new_product_name')
        new_category_id = request.form.get('new_category_id')


        if not new_product_name :
            flash_and_log('All fields are required.',category='error')
        
        
        else:

            try:

                new_category_id_int = int(new_category_id)

                selected_category = Category.query.get(new_category_id_int)

                if selected_category:

                    product.item_name = new_product_name
                    product.category_id = new_category_id


                        
                    try:
                        db.session.commit()
                        flash_and_log(f'Product "{new_product_name}" update successfully!', category='success')
                        return redirect(url_for('views.see_list'))
                        
                    except Exception as e:
                        db.session.rollback()
                        flash_and_log(f"Database error during update: {e}", category='error')
                        return "An error occurred during update.", 500
                    
                return redirect(url_for('view_item', product_id=product.id))

            

            except ValueError:
                flash_and_log("Invalid data format...", category='error')

        return redirect(url_for('views.see_list'))

    return render_template('update_item.html', user=current_user, categories = categories, products = product, category = category)







# Update an existing Category

@views.route("/update_categories/<id>", methods = ['GET', 'POST'])
@login_required
def update_categories(id):

    stocks = Stock.query.all()
    stock = db.session.get(Stock, id)

    products = Product.query.all()
    product = db.session.get(Product, id)

    categories = Category.query.all()
    category = db.session.get(Category, id)

    
    if not category:
        flash_and_log('Category does not exist!...', category='error')

    if request.method == 'POST':
        new_category_name = request.form.get('new_category_name')

        if not new_category_name :
            flash_and_log('All fields are required.',category='error')
        
        
        else:

            try:

                category.category_name = new_category_name

                    
                try:
                    db.session.commit()
                    flash_and_log(f'Category "{new_category_name}" update successfully!', category='success')
                    return redirect(url_for('views.see_list'))
                    
                except Exception as e:
                    db.session.rollback()
                    flash_and_log(f"Database error during update: {e}", category='error')
                    return "An error occurred during update.", 500

            

            except ValueError:
                flash_and_log("Invalid data format...", category='error')

        return redirect(url_for('views.see_list'))

    return render_template('update_categories.html', user=current_user, categories = category)





# Update an existing Location

@views.route("/update_location/<id>", methods = ['GET', 'POST'])
@login_required
def update_location(id):

    locations = Location.query.all()
    location = db.session.get(Location, id)

    
    if not location:
        flash_and_log('Category does not exist!...', category='error')

    if request.method == 'POST':
        new_location_name = request.form.get('new_location_name')

        if not new_location_name :
            flash_and_log('All fields are required.',category='error')
        
        
        else:

            try:

                location.location_name = new_location_name

                    
                try:
                    db.session.commit()
                    flash_and_log(f'Location "{new_location_name}" update successfully!', category='success')
                    return redirect(url_for('views.see_list'))
                    
                except Exception as e:
                    db.session.rollback()
                    flash_and_log(f"Database error during update: {e}", category='error')
                    return "An error occurred during update.", 500

            

            except ValueError:
                flash_and_log("Invalid data format...", category='error')

        return redirect(url_for('views.see_list'))

    return render_template('update_locations.html', user=current_user, locations = location)








# Update an existing Stock

@views.route("/update_stock/<id>", methods = ['GET', 'POST'])
@login_required
def update_stock(id):

    stocks = Stock.query.all()

    stock = db.session.get(Stock, id)

    product = Product.query.all()

    
    if not stock:
        flash_and_log('Stock does not exist!...', category='error')

    if request.method == 'POST':
        new_stock_name = request.form.get('new_stock_name')
        new_unit_price = request.form.get('new_unit_price')
        new_selling_price = request.form.get('new_selling_price')
        new_quantity = request.form.get('new_quantity')
        new_stock_description = request.form.get('new_stock_description')
        new_product_type = request.form.get('new_product_type')

        if not new_stock_name or not new_unit_price or not new_unit_price or not new_quantity or not new_product_type or not new_stock_description:
            flash_and_log('All fields are required.',category='error')
        
        
        if new_unit_price > new_selling_price:
            flash_and_log("Product sellig price must be higher than unit price...", category='error')
            return redirect(url_for('views.see_stocks'))
        
        else:

            try:
                # inputs type convertion
                new_product_id_int = int(new_product_type)

                selected_product = Product.query.get(new_product_id_int)

                if selected_product:

                    stock.stock_name = new_stock_name
                    stock.unit_price = float(new_unit_price)
                    stock.selling_price = float(new_selling_price)
                    stock.quantity = int(new_quantity)
                    stock.product_id = new_product_id_int
                    stock.stock_description = new_stock_description

                    
                    try:
                        db.session.commit()
                        flash_and_log(f'Stock "{new_stock_name}" update successfully!', category='success')
                        return redirect(url_for('views.see_stocks'))
                    
                    except Exception as e:
                        db.session.rollback()
                        flash_and_log(f"Database error during update: {e}", category='error')
                        return "An error occurred during update.", 500

                return redirect(url_for('view_item', stock_id=stock.id))



            

            except ValueError:
                flash_and_log("Invalid data format...", category='error')

        return redirect(url_for('views.see_stocks'))

    return render_template('update_stock.html', stock=stock, user=current_user, products=product)








# Delete Categories from invetory

@views.route("/delete_category/<id>")
@login_required
def delete_category(id):
    category = Category.query.filter_by(id=id).first()

    if not category:
        flash_and_log('Product does not exist!...', category='error')
    else:
        db.session.delete(category)
        db.session.commit()
        flash_and_log('Category deleted successfuly...', category='success')

    return redirect(url_for('views.see_list'))



# Delete Categories from invetory

@views.route("/delete_location/<id>")
@login_required
def delete_location(id):
    location = Location.query.filter_by(id=id).first()

    if not location:
        flash_and_log('Location does not exist!...', category='error')
    else:
        db.session.delete(location)
        db.session.commit()
        flash_and_log('Location deleted successfuly...', category='success')

    return redirect(url_for('views.see_list'))







# Delete Products from invetory

@views.route("/delete_product/<id>")
@login_required
def delete_product(id):
    item = Product.query.filter_by(id=id).first()

    if not item:
        flash_and_log('Product does not exist!...', category='error')
    else:
        db.session.delete(item)
        db.session.commit()
        flash_and_log('Product deleted successfuly...', category='success')

    return redirect(url_for('views.see_list'))







#Delete Stocks from inventory

@views.route("/delete_stocks/<id>")
@login_required
def delete_stocks(id):
    stock = Stock.query.filter_by(id=id).first()

    if not stock:
        flash_and_log('Stock does not exist!...', category='error')
    else:
        db.session.delete(stock)
        db.session.commit()
        flash_and_log('Stock deleted successfuly...', category='success')

    return redirect(url_for('views.see_stocks'))





# Sales proccessing

@views.route("/sale_process", methods = ['GET', 'POST'])
def sale_process():

    stocks = Stock.query.all()

    if request.method == 'POST':
        buyer_name = request.form.get('buyer_name')
        stock_id = request.form.get('stock_id')
        item_count = request.form.get('item_count')
        

        if not buyer_name or not stock_id or not item_count:
            flash_and_log('All fields are required.',category='error')
            return redirect(url_for('views.sale_process'))
        
        else:

            try:
                item_count_int = int(item_count)
                stock_id_int = int(stock_id)

                selected_stock = Stock.query.get(stock_id_int)

                if not selected_stock:
                    flash_and_log(f"Stock item with ID {stock_id_int} not found.", category='error')
                    return redirect(url_for('views.sale_process'))

                if selected_stock.quantity < item_count_int:
                    flash_and_log(f"Insufficient {selected_stock.stock_name} stock to complete the sale. Available: {selected_stock.quantity}", category='error')
                    return redirect(url_for('views.sale_process'))
                
                total_amount = item_count_int * selected_stock.selling_price


                new_sale = Sale(
                    sale_name = f"TEMP-{buyer_name}-{stock_id_int}",
                    total_amount = total_amount,
                    buyer_name = buyer_name
                )
                db.session.add(new_sale)
                db.session.flush()

                new_sale.sale_name = f"{new_sale.id}/{buyer_name}/{selected_stock.stock_name}/{item_count}" 


                new_sale_details = SaleDetail(
                    quantity_sold = item_count_int,
                    stock_id = stock_id_int, 
                    sale_id = new_sale.id, 
                    user_id = current_user.id
                )
                db.session.add(new_sale_details)
                


                current_saled_quantity = selected_stock.saled_quantity or 0
                selected_stock.saled_quantity = current_saled_quantity + item_count_int
                selected_stock.quantity -= item_count_int


                db.session.commit()
                flash_and_log("sale proccess completed...", category='success')
                return redirect(url_for('views.home'))

            except ValueError as e:
        
                db.session.rollback()
                flash_and_log(f"Sale failed: {e}", category='error')
                return redirect(url_for('views.sale_process'))
            
            except Exception as e:
                
                db.session.rollback()
                flash_and_log(f"An unexpected error occurred: {e}", category='error')
                return redirect(url_for('views.sale_process'))
        


        


    return render_template('sales.html', user=current_user, stocks=stocks)
 




@views.route("/flash_and_log")
@login_required
def flash_and_log(message, category = 'info'):

    log_data = {
        'message': message,
        'category': category
    }

    if current_user.is_authenticated:
        log_data['user_id'] = current_user.id

    try:
        new_log = LogMesssage(**log_data)
        db.session.add(new_log)
        db.session.commit()
    except Exception as e:
        print(f"Database logging failed: {e}")
        db.session.rollback() 
        

    flash(message, category=category)



# Notification store

@views.route("/check_notifications")
@login_required
def check_notifications():

    logMesssage = LogMesssage.query.all()

    sort_by = request.args.get('sort', 'id')
    direction = request.args.get('direction', 'asc')

    if sort_by == 'categories':
        column = LogMesssage.category
    elif sort_by == 'date':
        column = LogMesssage.date_created
    elif sort_by == 'message':
        column = LogMesssage.message

    else:
        # Default sort column
        column = LogMesssage.id

    if direction == 'desc':
        logMesssage = LogMesssage.query.order_by(desc(column)).all()
    else:
        # Default to ascending
        logMesssage = LogMesssage.query.order_by(asc(column)).all()


    return render_template("notifications.html", messages=logMesssage, user=current_user, current_sort=sort_by, current_direction=direction)




@views.route("/check_login_status")
@login_required
def check_login_status():

    userLoginLogs = UserLoginLog.query.all()


    return render_template("notifications.html", userLoginLogs=userLoginLogs, user=current_user)




# Chart genaration
@views.route("/sales_chart_page")
@login_required 
def sales_chart_page():
    
    stocks = Stock.query.all() 

    return render_template('see_chart.html', user=current_user, stocks=stocks)





@views.route("/sales_chart_data", methods=['POST'])
def sales_chart_data():

    stock_ids = request.form.getlist('stock_ids') # Expects a list of IDs
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')

    if not stock_ids:
        return jsonify({"error": "Please select at least one item."}), 400

    try:
        stock_ids_int = [int(i) for i in stock_ids if i]
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime(2020, 1, 1)
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            if end_date_str:
                end_date_inclusive = end_date + timedelta(days=1)
            else:
                end_date_inclusive = end_date
        else:
            end_date = datetime.now()

    except ValueError as e:
        return jsonify({"error": f"Invalid date or item ID format: {e}"}), 400


    query_result = db.session.query(
        SaleDetail.stock_id,
        func.date(SaleDetail.date_created).label('sale_day'), # Extract the date part
        func.sum(SaleDetail.quantity_sold).label('total_sold')
    ).join(Stock).filter(
        SaleDetail.stock_id.in_(stock_ids_int),
        SaleDetail.date_created >= start_date,
        SaleDetail.date_created <= end_date_inclusive
    ).group_by(
        SaleDetail.stock_id,
        'sale_day'
    ).order_by(
        'sale_day'
    ).all()

    # Get stock names for the legend
    stock_names = {
        s.id: s.stock_name 
        for s in Stock.query.filter(Stock.id.in_(stock_ids_int)).all()
    }
    
    # Convert results into a structured format (JSON-friendly list of dictionaries)
    chart_data = []
    for row in query_result:
        chart_data.append({
            'date': row.sale_day.strftime('%Y-%m-%d'), # Format date as string
            'item_name': stock_names.get(row.stock_id, f"Item {row.stock_id}"),
            'quantity': row.total_sold
        })

    # 4. Return the data as JSON
    return jsonify(chart_data)






# Download Sales reports

@views.route("/download_sales_report", methods=['GET'])
@login_required
def download_sales_report():
    report_data = db.session.query(
        Sale.sale_name,
        Sale.buyer_name,
        SaleDetail.quantity_sold,
        SaleDetail.date_created,
        Stock.stock_name,
        Stock.selling_price
        
    ).select_from(Sale
    ).join(SaleDetail, Sale.id == SaleDetail.sale_id
    ).join(Stock, SaleDetail.stock_id == Stock.id
    ).order_by(SaleDetail.date_created.desc()).all()

    print(f"--- SALES REPORT DEBUG ---")
    print(f"Number of records retrieved: {len(report_data)}")
    if report_data:
        print(f"First record: {report_data[0]}")
    else:
        print("Query returned an EMPTY list.")

    if not report_data:
        flash("No sales data found to generate a report.", category='info')
        return redirect(url_for('views.home'))

    proxy = StringIO()
    writer = csv.writer(proxy)

    header = ['Sale ID/Name', 'Buyer Name', 'Item Name', 'Quantity Sold', 
              'Price Per Unit', 'Total Value', 'Date/Time of Sale']
    writer.writerow(header)

    for row in report_data:
        sale_name, buyer_name, quantity_sold, date_created, stock_name, selling_price = row
        
        total_value = quantity_sold * selling_price
        
        data_row = [
            sale_name,
            buyer_name,
            stock_name,
            quantity_sold,
            f"{selling_price:.2f}",
            f"{total_value:.2f}",
            date_created.strftime('%Y-%m-%d %H:%M:%S')
        ]
        writer.writerow(data_row)
        
    csv_text = proxy.getvalue()
    byte_buffer = BytesIO()
    byte_buffer.write(csv_text.encode('utf-8')) 
    byte_buffer.seek(0)
    
    filename = f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return send_file(
        byte_buffer, 
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv'
    )


















@views.route("/about_us")
def about_us():

    return render_template('about.html', user=current_user)