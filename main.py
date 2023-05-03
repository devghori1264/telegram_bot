from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler, Updater
from prettytable import PrettyTable
import keys

print('Starting up bot...')

class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name, quantity, price_per_unit, description):
        self.items[item_name] = {
            'quantity': quantity,
            'price': price_per_unit,
            'description': description
        }

    def remove_item(self, item, quantity):
        if item not in self.items:
            raise ValueError("Item not found in inventory")
        if quantity > self.items[item]['quantity']:
            raise ValueError("Not enough items in inventory")
        self.items[item]['quantity'] -= quantity

    def get_items(self, product_name):
        return self.items.get(product_name, None)

    
def custom_command(update, context):
    update.message.reply_text('This is a custom command, you can add whatever text you want here.')

def handle_response(text) -> str:
    if 'hello' in text:
        return 'Hey there!'
    
    if 'how are you' in text:
        return 'I\'m good!'

    return 'I don\'t understand'

def handle_message(update, context):
    message_type = update.message.chat.type
    text = str(update.message.text).lower()
    response = ''

    print(f'User ({update.message.chat.id}) says: "{text}" in: {message_type}')

    if message_type == 'group':
        if '@mataji_general_store_bot' in text:
            new_text = text.replace('@mataji_general_store_bot', '').strip()
            response = handle_response(new_text)
    else:
        response = handle_response(text)

    update.message.reply_text(response)


def error(update, context):
    print(f'Update {update} caused error {context.error}')
      

inventory = Inventory()
inventory.add_item("Rice", 50, 2.5, "Long grain white rice")
inventory.add_item("Sugar", 20, 3, "Granulated white sugar")
inventory.add_item("Flour", 30, 2, "All-purpose flour")
inventory.add_item("Salt", 40, 1, "Fine sea salt")
inventory.add_item("Eggs", 60, 0.5, "Large brown eggs")
inventory.add_item("Milk", 25, 2.5, "Whole milk")
inventory.add_item("Butter", 15, 4, "Unsalted butter")
inventory.add_item("Bread", 10, 3, "Sourdough bread")
inventory.add_item("Cheese", 20, 5, "Cheddar cheese")
inventory.add_item("Chicken", 5, 10, "Boneless chicken breast")
inventory.add_item("Beef", 5, 12, "Ground beef")
inventory.add_item("Fish", 5, 8, "Salmon fillet")
inventory.add_item("Vegetables", 20, 1.5, "Mixed vegetables")
inventory.add_item("Fruits", 30, 2, "Assorted fruits")
inventory.add_item("Water", 40, 1, "Bottled water")

orders = {}

currency_symbol = keys.currency

def start(update, context):
    """Send a message when the command /start is issued."""
    welcome_message = "Hello and welcome to our General Store bot! We're thrilled to have you here. Our bot is designed to help make your shopping experience as easy and convenient as possible. we provide free delivery for 2 km area. You can browse our products, place orders, and track your deliveries all in one place. If you have any questions or need assistance, our friendly customer support team is always ready to help. Thank you for choosing our General Store and happy shopping!"
    context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message)


def start_command(update, context):
    update.message.reply_text('Welcome to our store!')

def help_command(update, context):
    commands = [
        "/start - Welcome to store",
        "/help - List of commands",
        "/inventory - List of available products",
        "/product_request - Customers who don't find their product in inventory list can request owner by this command, owner will try to provide that. Usage: product_request <product_name>",
        "/order - This command will add a product to the cart. Usage: order <product_name> <quantity>",
        "/cart - This command will show the products that are currently in the cart.",
        "/checkout - This command will finalize the order and show the total price.",
        "/cancel_order - This command will cancel the order and remove all the items from the cart.",
        "/contact - This command will provide contact details of store.",
    ]
    help_text = '\n'.join(commands)
    update.message.reply_text(help_text)
    

def inventory_command(update, context):
    items_table = PrettyTable()
    items_table.field_names = ["Item", "Quantity", "Price", "Description"]
    
    for item_name in inventory.items:
        item = inventory.items[item_name]
        items_table.add_row([item_name, item['quantity'], f"{item['price']:.2f} {currency_symbol}", item['description']])

    update.message.reply_text(f'Available products:\n{items_table}')
    

def product_request_command(update, context):
    product_name = context.args[0]
    update.message.reply_text(f'Thank you for requesting {product_name}. We will try to add this product to our inventory soon!')

def order_command(update, context):
    chat_id = update.message.chat_id
    args = context.args

    if len(args) != 2:
        update.message.reply_text('Please provide in the following manner: /order <product_name> <quantity>')
        return

    product_name = args[0]
    quantity = args[1]

    item = inventory.get_items(product_name)

    if item is None:
        update.message.reply_text('Product not found')
        return

    if not quantity.isdigit() or int(quantity) <= 0:
        update.message.reply_text('Invalid quantity')
        return

    if int(quantity) > item['quantity']:
        update.message.reply_text('Not enough stock')
        return

    price = item['price']
    total_price = price * int(quantity)

    orders[chat_id] = orders.get(chat_id, {})
    orders[chat_id][product_name] = orders[chat_id].get(product_name, 0) + int(quantity)

    update.message.reply_text(f'{quantity} {product_name} added to cart. Total: {total_price} {keys.currency}')


def bill_command(update: Update, context: CallbackContext):
    # Get user information
    user = update.effective_user
    first_name = user.first_name if user.first_name else ''
    last_name = user.last_name if user.last_name else ''
    username = user.username if user.username else ''
    user_id = user.id

    # Create the invoice
    invoice = {
        'title': 'Product/Service Name',
        'description': 'Description of Product/Service',
        'start_parameter': 'bot-invoice',
        'currency': 'USD',
        'total_amount': 10000 
    }

    invoice_button = InlineKeyboardButton(
        text='Pay Now',
        pay=True,
        invoice_data=serialize_invoice(invoice),
        payload=f'{first_name} {last_name} ({username}) - {user_id}'
    )

    keyboard = [[invoice_button]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        text='Please select the following button to pay your bill:',
        reply_markup=reply_markup
    )

def serialize_invoice(invoice):
    return str(invoice).replace("'", "\"")

def get_product_name(update, context):
    product_name = update.message.text.lower()
    if product_name not in inventory:
        update.message.reply_text('Sorry, that product is not available.')
        return ConversationHandler.END
    update.message.reply_text(f'You have selected {inventory[product_name]["name"]}. Please enter the quantity.')
    context.user_data['product'] = inventory[product_name]
    return 'GET_QUANTITY'

def get_quantity(update, context):
    quantity = int(update.message.text)
    product = context.user_data['product']
    if quantity > product['quantity']:
        update.message.reply_text('Sorry, there is not enough quantity available.')
        return ConversationHandler.END
    context.user_data['quantity'] = quantity
    if context.user_data['chat_id'] not in orders:
        orders[context.user_data['chat_id']] = {}
    orders[context.user_data['chat_id']][product['name']] = {'quantity': quantity, 'price': product['price']}
    update.message.reply_text(f'{quantity} {product["name"]} added to cart.')
    return ConversationHandler.END

def cart_command (update, context):
    cart_items = {}
    for order in orders:
        item, quantity = order
        if item not in cart_items:
            cart_items[item] = 0
        cart_items[item] += quantity
    items_str = ""
    for item, quantity in cart_items.items():
        items_str += f"{item}: {quantity}\n"
    return items_str

def cancel_command(update, context):
    chat_id = update.message.chat_id
    user_data = context.user_data
    if 'cart' in user_data:
        cart = user_data['cart']
        if cart:
            user_data['cart'] = []
            context.bot.send_message(chat_id=chat_id, text='Your cart has been cleared.')
        else:
            context.bot.send_message(chat_id=chat_id, text='Your cart is already empty.')
    else:
        context.bot.send_message(chat_id=chat_id, text='Your cart is already empty.')

def status_command(update, context):
    chat_id = update.message.chat_id
    user_data = context.user_data
    message = 'Product status:\n'
    for product in inventory:
        message += f"{product['name']} - {product['status']}\n"
    context.bot.send_message(chat_id=chat_id, text=message)

def product_details_command(update, context):
    chat_id = update.message.chat_id
    user_data = context.user_data
    if 'product_name' in user_data:
        product_name = user_data['product_name']
        product = next((p for p in inventory if p['name'] == product_name), None)
        if product:
            message = f"{product['name']} - {product['description']}\nPrice: {product['price']:.2f} {product['currency']}"
        else:
            message = f"Product '{product_name}' not found in inventory."
    else:
        message = 'Please specify a product name.'
    context.bot.send_message(chat_id=chat_id, text=message)
    

def checkout_command(update, context):
    chat_id = update.message.chat_id
    if chat_id not in orders:
        update.message.reply_text('Your cart is empty. Please add some items to your cart using /order command.')
        return
    
    total_price = 0
    order_details = []
    for item, quantity in orders[chat_id].items():
        item_price = inventory.items[item]['price']
        item_total_price = item_price * quantity
        total_price += item_total_price
        order_details.append(f"{item} x {quantity} = {item_total_price} {currency_symbol}")
    
    order_details.append(f"Total Price: {total_price} {currency_symbol}")
    order_summary = '\n'.join(order_details)
    
    update.message.reply_text(f"Your Order Summary:\n{order_summary}\nPlease confirm your order by sending /confirm command.")

def contact(update, context):
    contact_info = "Address: 3. Madhav shopping, godadara, surat\nContact number: 9328290952\nEmail: matajistore11@gmail.com"
    context.bot.send_message(chat_id=update.effective_chat.id, text=contact_info)


def confirm_command(update, context):
    chat_id = update.message.chat_id
    if chat_id not in orders:
        update.message.reply_text('Your cart is empty. Please add some items to your cart using /order command.')
        return
    
    # Do something with the order, like save it to a database or send a notification to the store owner
    # Here we are just clearing the cart and sending a confirmation message to the user
    orders.pop(chat_id)
    update.message.reply_text('Thank you for your order! Your order has been confirmed and will be delivered soon.')


if __name__ == '__main__':
    updater = Updater(keys.token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler('start', start_command))
    dp.add_handler(CommandHandler('help', help_command))
    dp.add_handler(CommandHandler('inventory', inventory_command))
    dp.add_handler(CommandHandler('product_request', product_request_command))
    dp.add_handler(CommandHandler('order', order_command))
    dp.add_handler(CommandHandler('bill', bill_command))
    dp.add_handler(CommandHandler('cart', cart_command))
    dp.add_handler(CommandHandler('cancel', cancel_command))
    dp.add_handler(CommandHandler('status', status_command))
    dp.add_handler(CommandHandler('product_details', product_details_command))
    dp.add_handler(CommandHandler('checkout', checkout_command))
    dp.add_handler(CommandHandler('contact', contact))
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    dp.add_error_handler(error)
    updater.start_polling(1.0)
    updater.idle()
