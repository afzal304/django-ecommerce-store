// Get all buttons with class "update-cart"
var updateBtns = document.getElementsByClassName('update-cart');
console.log("Initial number of updateBtns:", updateBtns.length);

// Add event listeners to each update button
for (let i = 0; i < updateBtns.length; i++) {
  console.log("Attaching listener to elements:", updateBtns[i]);
  updateBtns[i].addEventListener('click', function () {
    console.log("🖱️ Clicked element:", this);
    console.log("📌 Number of updateBtns after click:", updateBtns.length);

    var productId = this.dataset.product;
    var action = this.dataset.action;
    var variantId = this.dataset.variant || null; // 👈 NEW: capture variantId if set

    console.log("➡️ Sending to updateCart:", { productId, action, variantId });
    updateCart(productId, action, variantId);
  });
}

// ✅ Updated fetch call with CSRF token
function updateCart(productId, action, variantId = null) {
  //console.log("🛒 updateCart() called");
  //console.log("➡️ Product ID:", productId, "| Action:", action, "| Variant ID:", variantId);
  console.log("== CART REQUEST ==");
  console.log("Product ID: ", productId);
  console.log("Action: ", action);
  console.log("Variant ID: ", variantId);
  console.log("CSRFToken: ", csrftoken);
  fetch('/update_item/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken   // 👈 Important
    },
    body: JSON.stringify({
      'productId': productId, 
      'variantId': variantId, 
      'action': action
    })
  })
  .then(response => {
    console.log("== SERVER Response ==");
    console.log("Response: ", response.status);
    return response.json();
  })
  .then(data => {
    console.log("== RESPONSE DATA ==");
    console.log("Full data", data);
    console.log("Cart Items Count", data.cart_items);
    console.log("Cart Total", data.cart_total);

    if (data.error) {
      console.warn("⚠️ Error from server:", data.message || data.error);

      const stockMsg = document.getElementById(`stock-msg-${productId}`);
      const detailstockMsg = document.getElementById("stock-msg-detail");

      if (stockMsg) {
        stockMsg.innerText = data.message || "Out of stock";
        stockMsg.classList.add("stock-error-msg");
        setTimeout(() => {
          stockMsg.innerText = "";
        }, 3000);
      }

      if(detailstockMsg){
        detailstockMsg.innerText = data.message ||"out of stock";
        detailstockMsg.classList.add("stock-error-msg");
        setTimeout(() => {
          detailstockMsg.innerText = "";
        }, 3000);

      }
      return; // stop further cart updates
    }
 
    // Update navbar count
    document.getElementById('cart-total').innerText = data.cart_items;

    // Update total in header (cart.html top)
    let cartItemsCount = document.getElementById('cart-items-count');
    let cartTotalPrice = document.getElementById('cart-total-price');
    if (cartItemsCount && cartTotalPrice) {
      cartItemsCount.innerText = data.cart_items;
      cartTotalPrice.innerText = data.cart_total.toFixed(2);
    }

    // ✅ Use variantId if available, otherwise fallback to productId 120
    let rowKey = variantId ? `variant-${variantId}` : `product-${productId}`;

    let qtyElem = document.querySelector(`#qty-${rowKey}`);
    let itemTotalElem = document.querySelector(`#item-total-${rowKey}`);

    if (qtyElem && itemTotalElem) {
      if (data.quantity > 0) {
        qtyElem.innerText = data.quantity;
        itemTotalElem.innerText = data.item_total.toFixed(2);
      } else {
        // Remove row if qty is 0
        let row = document.querySelector(`#cart-row-${rowKey}`);
        if (row) {
          row.remove();
          console.log(`🗑️ Removed row for ${rowKey}`);
        }
      }
    }
  });
}
