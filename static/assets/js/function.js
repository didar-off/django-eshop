$(document).ready(function(){
    const Toast = Swal.mixin({
        toast: true,
        position: "top",
        showConfirmButton: false,
        timer: 5000,
        timerProgressBar: true,
    });
    
    
    function generateCartId() {
        const ls_cartid = localStorage.getItem("cartId");

        if (ls_cartid === null) {
            var cartId = "";

            for (var i =0; i < 10; i++) {
                cartId += Math.floor(Math.random() * 10);
            }

            localStorage.setItem("cartId", cartId);
        }

        return ls_cartid || cartId
    }


    $(document).on("click", ".add", function(){
        const button_el = $(this)
        const id = button_el.attr("data-id")
        const qty = $(".quantity").val()
        const cart_id = generateCartId()

        console.log("Product ID:", id);
        console.log("Quantity:", qty);
        console.log("Cart ID:", cart_id);

        $.ajax({
            url: '/add-to-cart/',
            data: {
                id: id,
                qty: qty,
                cart_id: cart_id,
            },
            beforeSend: function() {
                button_el.html("Adding To Cart <i class='fas fa-spinner fa-spin ms-2'></i>")
            },
            success: function(response){
                console.log(response);
                Toast.fire({
                    icon: "success",
                    title: response?.message,
                });
                
                button_el.html("<i class='fa-solid fa-check'></i>");
                button_el.prop('disabled', true);
                $(".total_cart_items").text(response?.total_cart_items);
            },
            error: function(xhr, status, error){
                console.log("Error status: ", xhr.status);
                console.log("Response Text: ", xhr.responseText);

                let errorResponse = JSON.parse(xhr.responseText);
                Toast.fire({
                    icon: "success",
                    title: errorResponse?.error,
                });
            },
        });
    });


    $(document).on("change", ".update_cart_qty", function(){
        const input_el  = $(this);
        const item_id = input_el.attr("data-item_id");
        const product_id = input_el.attr("data-product_id");
        const qty = input_el.val()
        const cart_id = generateCartId();

        console.log("Item ID:", item_id);
        console.log("Product ID:", product_id);
        console.log("Quantity:", qty);
        console.log("Cart ID:", cart_id);

        $.ajax({
            url: '/add-to-cart/',
            data: {
                id: product_id,
                qty: qty,
                cart_id: cart_id,
            },
            success: function(response){
                console.log(response);
                Toast.fire({
                    icon: "success",
                    title: response?.message,
                });

                $(".item_sub_total_" + item_id).text(response.item_sub_total);
                $(".cart_sub_total").text(response.cart_sub_total);             
            },
            error: function(xhr, status, error){
                console.log("Error status: ", xhr.status);
                console.log("Response Text: ", xhr.responseText);

                let errorResponse = JSON.parse(xhr.responseText);
                Toast.fire({
                    icon: "success",
                    title: errorResponse?.error,
                });
            },
        });

    });


    $(document).on("click", ".delete_cart_item", function(){
        const button_el = $(this);
        const item_id = button_el.attr("data-item_id");
        const product_id = button_el.attr("data-product_id");
        const cart_id = generateCartId();

        console.log('Product ID: ', product_id);
        console.log('Item ID: ', item_id);
        console.log('Cart ID: ', cart_id);


        $.ajax({
            url: '/delete-cart-item/',
            data: {
                id: product_id,
                item: item_id,
                cart_id: cart_id,
            },
            beforeSend: function() {
                button_el.html("<i class='fas fa-spinner fa-spin ms-2'></i>")
            },
            success: function(response){
                console.log(response);
                Toast.fire({
                    icon: "success",
                    title: response?.message,
                });
                $(".total_cart_items").text(response?.total_cart_items);
                $(".cart_sub_total").text(response?.cart_sub_total);
                $(".item_div_" + item_id).addClass("d-none");
            },
        })
    });
});