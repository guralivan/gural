
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // Обработка эндпоинта воронки продаж
    if (url.pathname === '/api/v1/sales-funnel') {
      return handleSalesFunnel(request, env);
    }
    
    // Обработка заказов
    if (url.pathname === '/api/v1/supplier/orders') {
      return handleOrders(request, env);
    }
    
    // Обработка продаж
    if (url.pathname === '/api/v1/supplier/sales') {
      return handleSales(request, env);
    }
    
    // Обработка остатков
    if (url.pathname === '/api/v3/supplies/stocks') {
      return handleStocks(request, env);
    }
    
    // Обработка поставок
    if (url.pathname === '/api/v3/supplies') {
      return handleSupplies(request, env);
    }
    
    // Обработка возвратов
    if (url.pathname === '/api/v1/supplier/returns') {
      return handleReturns(request, env);
    }
    
    // Обработка статистики по периодам
    if (url.pathname === '/api/v5/supplier/reportDetailByPeriod') {
      return handleReportDetailByPeriod(request, env);
    }
    
    // Обработка категорий товаров
    if (url.pathname === '/api/lite/products/wb_categories') {
      return handleCategories(request, env);
    }
    
    // Обработка поисковых запросов
    if (url.pathname === '/api/v1/search-queries') {
      return handleSearchQueries(request, env);
    }
    
    // Обработка скрытых товаров
    if (url.pathname === '/api/v1/hidden-products') {
      return handleHiddenProducts(request, env);
    }
    
    // Обработка доли бренда
    if (url.pathname === '/api/v1/brand-share') {
      return handleBrandShare(request, env);
    }
    
    // Для остальных эндпоинтов - проксирование
    const target = new URL(url.pathname + url.search, env.WB_BASE);

    const bodyText = await request.text();
    const headers = new Headers();
    const ct = request.headers.get("content-type");
    if (ct) headers.set("content-type", ct);

    const authValue = env.WB_BEARER === "true" ? `Bearer ${env.WB_TOKEN}` : env.WB_TOKEN;
    headers.set(env.WB_AUTH_HEADER || "Authorization", authValue);

    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Headers": "*",
          "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
      });
    }

    const upstream = await fetch(target, {
      method: request.method,
      headers,
      body: ["GET", "HEAD"].includes(request.method) ? undefined : bodyText,
    });

    const resHeaders = new Headers(upstream.headers);
    resHeaders.set("Access-Control-Allow-Origin", "*");
    resHeaders.set("Access-Control-Allow-Headers", "*");
    resHeaders.set("Access-Control-Allow-Methods", "GET,POST,OPTIONS");

    return new Response(await upstream.arrayBuffer(), {
      status: upstream.status,
      headers: resHeaders,
    });
  }
}

// Функция для обработки заказов
async function handleOrders(request, env) {
  const url = new URL(request.url);
  const dateFrom = url.searchParams.get('dateFrom');
  const dateTo = url.searchParams.get('dateTo');
  
  if (!dateFrom || !dateTo) {
    return new Response(JSON.stringify({
      success: false,
      error: "Параметры dateFrom и dateTo обязательны"
    }), {
      status: 400,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }
  
  try {
    // Получаем реальные данные
    const targetUrl = new URL(`/api/v1/supplier/orders?dateFrom=${dateFrom}&dateTo=${dateTo}`, env.WB_BASE);
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'Authorization': env.WB_BEARER === "true" ? `Bearer ${env.WB_TOKEN}` : env.WB_TOKEN
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log(`Orders API success: ${data.length} records`);
      return new Response(JSON.stringify(data), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    } else {
      // Возвращаем ошибку API
      console.log(`Orders API error: ${response.status}`);
      return new Response(JSON.stringify({
        success: false,
        error: `API недоступен: ${response.status}`,
        details: "Не удалось получить данные заказов"
      }), {
        status: response.status,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }
    
  } catch (error) {
    console.log('Orders error:', error);
    return new Response(JSON.stringify({
      success: false,
      error: "Ошибка соединения",
      details: error.message
    }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }
}

// Функция для обработки продаж
async function handleSales(request, env) {
  const url = new URL(request.url);
  const dateFrom = url.searchParams.get('dateFrom');
  const dateTo = url.searchParams.get('dateTo');
  
  if (!dateFrom || !dateTo) {
    return new Response(JSON.stringify({
      success: false,
      error: "Параметры dateFrom и dateTo обязательны"
    }), {
      status: 400,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }
  
  try {
    // Получаем реальные данные
    const targetUrl = new URL(`/api/v1/supplier/sales?dateFrom=${dateFrom}&dateTo=${dateTo}`, env.WB_BASE);
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'Authorization': env.WB_BEARER === "true" ? `Bearer ${env.WB_TOKEN}` : env.WB_TOKEN
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log(`Sales API success: ${data.length} records`);
      return new Response(JSON.stringify(data), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    } else {
      // Возвращаем ошибку API
      console.log(`Sales API error: ${response.status}`);
      return new Response(JSON.stringify({
        success: false,
        error: `API недоступен: ${response.status}`,
        details: "Не удалось получить данные продаж"
      }), {
        status: response.status,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }
    
  } catch (error) {
    console.log('Sales error:', error);
    return new Response(JSON.stringify({
      success: false,
      error: "Ошибка соединения",
      details: error.message
    }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }
}

// Функция для обработки остатков
async function handleStocks(request, env) {
  try {
    // Получаем реальные данные
    const targetUrl = new URL('/api/v3/supplies/stocks', env.WB_BASE);
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'Authorization': env.WB_BEARER === "true" ? `Bearer ${env.WB_TOKEN}` : env.WB_TOKEN
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log(`Stocks API success: ${data.length} records`);
      return new Response(JSON.stringify(data), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    } else {
      // Возвращаем ошибку API
      console.log(`Stocks API error: ${response.status}`);
      return new Response(JSON.stringify({
        success: false,
        error: `API недоступен: ${response.status}`,
        details: "Не удалось получить данные остатков"
      }), {
        status: response.status,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }
    
  } catch (error) {
    console.log('Stocks error:', error);
    return new Response(JSON.stringify({
      success: false,
      error: "Ошибка соединения",
      details: error.message
    }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }
}

// Функция для обработки поставок
async function handleSupplies(request, env) {
  try {
    const targetUrl = new URL('/api/v3/supplies', env.WB_BASE);
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'Authorization': env.WB_BEARER === "true" ? `Bearer ${env.WB_TOKEN}` : env.WB_TOKEN
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      return new Response(JSON.stringify(data), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    } else {
      return new Response(JSON.stringify({
        success: false,
        error: `API недоступен: ${response.status}`,
        details: "Не удалось получить данные поставок"
      }), {
        status: response.status,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      error: "Ошибка соединения",
      details: error.message
    }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }
}

// Функция для обработки возвратов
async function handleReturns(request, env) {
  try {
    const targetUrl = new URL('/api/v1/supplier/returns', env.WB_BASE);
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'Authorization': env.WB_BEARER === "true" ? `Bearer ${env.WB_TOKEN}` : env.WB_TOKEN
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      return new Response(JSON.stringify(data), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    } else {
      return new Response(JSON.stringify({
        success: false,
        error: `API недоступен: ${response.status}`,
        details: "Не удалось получить данные возвратов"
      }), {
        status: response.status,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      error: "Ошибка соединения",
      details: error.message
    }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }
}

// Функция для обработки детальной статистики по периодам
async function handleReportDetailByPeriod(request, env) {
  const url = new URL(request.url);
  const dateFrom = url.searchParams.get('dateFrom');
  const dateTo = url.searchParams.get('dateTo');
  
  if (!dateFrom || !dateTo) {
    return new Response(JSON.stringify({
      success: false,
      error: "Параметры dateFrom и dateTo обязательны"
    }), {
      status: 400,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }
  
  try {
    const targetUrl = new URL(`/api/v5/supplier/reportDetailByPeriod?dateFrom=${dateFrom}&dateTo=${dateTo}`, env.WB_BASE);
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'Authorization': env.WB_BEARER === "true" ? `Bearer ${env.WB_TOKEN}` : env.WB_TOKEN
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      return new Response(JSON.stringify(data), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    } else {
      return new Response(JSON.stringify({
        success: false,
        error: `API недоступен: ${response.status}`,
        details: "Не удалось получить детальную статистику"
      }), {
        status: response.status,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      error: "Ошибка соединения",
      details: error.message
    }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }
}

// Функция для обработки категорий товаров
async function handleCategories(request, env) {
  try {
    const targetUrl = new URL('/api/lite/products/wb_categories', env.WB_BASE);
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'Authorization': env.WB_BEARER === "true" ? `Bearer ${env.WB_TOKEN}` : env.WB_TOKEN
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      return new Response(JSON.stringify(data), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    } else {
      return new Response(JSON.stringify({
        success: false,
        error: `API недоступен: ${response.status}`,
        details: "Не удалось получить категории товаров"
      }), {
        status: response.status,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      error: "Ошибка соединения",
      details: error.message
    }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }
}

// Функция для обработки поисковых запросов
async function handleSearchQueries(request, env) {
  try {
    const targetUrl = new URL('/api/v1/search-queries', env.WB_BASE);
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'Authorization': env.WB_BEARER === "true" ? `Bearer ${env.WB_TOKEN}` : env.WB_TOKEN
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      return new Response(JSON.stringify(data), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    } else {
      return new Response(JSON.stringify({
        success: false,
        error: `API недоступен: ${response.status}`,
        details: "Не удалось получить данные поисковых запросов"
      }), {
        status: response.status,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      error: "Ошибка соединения",
      details: error.message
    }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }
}

// Функция для обработки скрытых товаров
async function handleHiddenProducts(request, env) {
  try {
    const targetUrl = new URL('/api/v1/hidden-products', env.WB_BASE);
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'Authorization': env.WB_BEARER === "true" ? `Bearer ${env.WB_TOKEN}` : env.WB_TOKEN
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      return new Response(JSON.stringify(data), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    } else {
      return new Response(JSON.stringify({
        success: false,
        error: `API недоступен: ${response.status}`,
        details: "Не удалось получить данные скрытых товаров"
      }), {
        status: response.status,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      error: "Ошибка соединения",
      details: error.message
    }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }
}

// Функция для обработки доли бренда
async function handleBrandShare(request, env) {
  try {
    const targetUrl = new URL('/api/v1/brand-share', env.WB_BASE);
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'Authorization': env.WB_BEARER === "true" ? `Bearer ${env.WB_TOKEN}` : env.WB_TOKEN
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      return new Response(JSON.stringify(data), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    } else {
      return new Response(JSON.stringify({
        success: false,
        error: `API недоступен: ${response.status}`,
        details: "Не удалось получить данные доли бренда"
      }), {
        status: response.status,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      error: "Ошибка соединения",
      details: error.message
    }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }
}

// Функция для обработки эндпоинта воронки продаж
async function handleSalesFunnel(request, env) {
  const url = new URL(request.url);
  const dateFrom = url.searchParams.get('dateFrom');
  const dateTo = url.searchParams.get('dateTo');
  
  if (!dateFrom || !dateTo) {
    return new Response(JSON.stringify({
      success: false,
      error: "Параметры dateFrom и dateTo обязательны"
    }), {
      status: 400,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }
  
  try {
    // Получаем данные заказов
    const ordersUrl = new URL(`/api/v1/supplier/orders?dateFrom=${dateFrom}&dateTo=${dateTo}`, env.WB_BASE);
    const ordersResponse = await fetch(ordersUrl, {
      method: 'GET',
      headers: {
        'Authorization': env.WB_BEARER === "true" ? `Bearer ${env.WB_TOKEN}` : env.WB_TOKEN
      }
    });
    
    // Получаем данные продаж
    const salesUrl = new URL(`/api/v1/supplier/sales?dateFrom=${dateFrom}&dateTo=${dateTo}`, env.WB_BASE);
    const salesResponse = await fetch(salesUrl, {
      method: 'GET',
      headers: {
        'Authorization': env.WB_BEARER === "true" ? `Bearer ${env.WB_TOKEN}` : env.WB_TOKEN
      }
    });
    
    let orders = [];
    let sales = [];
    let ordersSuccess = false;
    let salesSuccess = false;
    
    // Обрабатываем заказы
    if (ordersResponse.ok) {
      orders = await ordersResponse.json();
      ordersSuccess = true;
      console.log(`Заказы получены: ${orders.length} записей`);
    } else {
      console.log(`Ошибка заказов: ${ordersResponse.status}`);
    }
    
    if (salesResponse.ok) {
      sales = await salesResponse.json();
      salesSuccess = true;
      console.log(`Продажи получены: ${sales.length} записей`);
    } else {
      console.log(`Ошибка продаж: ${salesResponse.status}`);
    }
    
    // Создаем данные воронки продаж
    if (ordersSuccess || salesSuccess) {
      console.log(`Creating funnel data from orders: ${orders.length}, sales: ${sales.length}`);
      const data = createProductData(orders, sales, dateFrom, dateTo);
      console.log(`Funnel data created: ${data.data.length} records`);
      
      return new Response(JSON.stringify(data), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Headers": "*",
          "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
      });
    } else {
      throw new Error(`Не удалось получить данные: Orders: ${ordersResponse.status}, Sales: ${salesResponse.status}`);
    }
    
  } catch (error) {
    console.log('Error creating product data:', error);
    
    return new Response(JSON.stringify({
      success: false,
      error: "Не удалось получить данные по товарам",
      details: error.message
    }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
      },
    });
  }
}

// Функция для создания данных по товарам
function createProductData(orders, sales, dateFrom, dateTo) {
  console.log(`Creating product data from ${orders.length} orders and ${sales.length} sales`);
  
  // Группируем данные по товарам и дням
  const productDailyData = {};
  
  // Обрабатываем заказы
  orders.forEach(order => {
    const dateStr = order.date.split('T')[0];
    const nmId = order.nmId;
    
    if (!productDailyData[nmId]) {
      productDailyData[nmId] = {};
    }
    
    if (!productDailyData[nmId][dateStr]) {
      productDailyData[nmId][dateStr] = {
        orders: 0,
        sales: 0,
        orders_amount: 0,
        sales_amount: 0
      };
    }
    
    productDailyData[nmId][dateStr].orders += 1;
    productDailyData[nmId][dateStr].orders_amount += (order.totalPrice || 0);
  });
  
  // Обрабатываем продажи
  sales.forEach(sale => {
    const dateStr = sale.date.split('T')[0];
    const nmId = sale.nmId;
    
    if (!productDailyData[nmId]) {
      productDailyData[nmId] = {};
    }
    
    if (!productDailyData[nmId][dateStr]) {
      productDailyData[nmId][dateStr] = {
        orders: 0,
        sales: 0,
        orders_amount: 0,
        sales_amount: 0
      };
    }
    
    productDailyData[nmId][dateStr].sales += 1;
    productDailyData[nmId][dateStr].sales_amount += (sale.finishedPrice || sale.priceWithDisc || 0);
  });
  
  // Создаем результат
  const result = [];
  
  Object.keys(productDailyData).forEach(nmId => {
    const product = productDailyData[nmId];
    
    Object.keys(product).forEach(dateStr => {
      const dayData = product[dateStr];
      
      result.push({
        date: dateStr,
        nmId: nmId,
        supplierArticle: orders.find(o => o.nmId == nmId)?.supplierArticle || sales.find(s => s.nmId == nmId)?.supplierArticle || '',
        brand: orders.find(o => o.nmId == nmId)?.brand || sales.find(s => s.nmId == nmId)?.brand || '',
        subject: orders.find(o => o.nmId == nmId)?.subject || sales.find(s => s.nmId == nmId)?.subject || '',
        orders: dayData.orders,
        sales: dayData.sales,
        orders_amount: Math.round(dayData.orders_amount * 100) / 100,
        sales_amount: Math.round(dayData.sales_amount * 100) / 100,
        conversion_rate: dayData.orders > 0 ? Math.round((dayData.sales / dayData.orders) * 100 * 100) / 100 : 0
      });
    });
  });
  
  return {
    success: true,
    data: result,
    message: "Данные по товарам (nmId) на основе реальных заказов и продаж",
    source: "orders_and_sales_by_product",
    summary: {
      total_products: Object.keys(productDailyData).length,
      total_orders: orders.length,
      total_sales: sales.length,
      total_orders_amount: Math.round(orders.reduce((sum, order) => sum + (order.totalPrice || 0), 0) * 100) / 100,
      total_sales_amount: Math.round(sales.reduce((sum, sale) => sum + (sale.finishedPrice || sale.priceWithDisc || 0), 0) * 100) / 100
    }
  };
}