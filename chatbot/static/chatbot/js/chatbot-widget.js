(function(){
    'use strict';

    var CFG = window.__ESCO_CHATBOT_CONFIG || {};
    if (!CFG.enabled) return;

    var root = document.getElementById('esco-chatbot-root');
    if (!root) return;

    var conversationId = null;
    var isOpen = false;
    var isSending = false;
    var isRecording = false;
    var mediaRecorder = null;
    var audioChunks = [];

    // Apply theme colors
    document.documentElement.style.setProperty('--chatbot-primary', CFG.primary_color || '#1e88e5');
    document.documentElement.style.setProperty('--chatbot-secondary', CFG.secondary_color || '#ffffff');
    document.documentElement.style.setProperty('--chatbot-bubble-bg', CFG.bubble_bg_color || CFG.primary_color || '#1e88e5');
    document.documentElement.style.setProperty('--chatbot-bubble-icon-color', CFG.bubble_icon_color || '#ffffff');
    document.documentElement.style.setProperty('--chatbot-avatar-icon-color', CFG.avatar_icon_color || '#ffffff');

    // Build HTML
    var dir = CFG.direction || 'rtl';
    var pos = CFG.position || 'bottom-right';
    var sizeClass = 'size-' + (CFG.bubble_size || 'medium');
    var isAr = CFG.language === 'ar';
    var placeholderText = isAr ? 'اكتب رسالتك...' : 'Type your message...';
    var onlineText = isAr ? 'متصل الآن' : 'Online now';
    var viewProductText = isAr ? 'عرض المنتج' : 'View Product';

    var avatarIcon = CFG.avatar_icon || 'fas fa-robot';
    var bubbleIcon = CFG.bubble_icon || 'fas fa-comments';
    var avatarHTML = CFG.avatar_url
        ? '<img src="'+CFG.avatar_url+'" alt="bot">'
        : '<i class="'+avatarIcon+'" style="color:'+( CFG.avatar_icon_color || '#ffffff')+'"></i>';

    root.innerHTML =
        '<button class="esco-chatbot-bubble '+pos+' '+sizeClass+'" id="escoChatBubble" aria-label="Chat">' +
            '<span class="bubble-icon-open"><i class="'+bubbleIcon+'"></i></span>' +
            '<span class="bubble-icon-close"><i class="fas fa-times"></i></span>' +
        '</button>' +
        '<div class="esco-chatbot-window '+pos+'" id="escoChatWindow" dir="'+dir+'">' +
            '<div class="esco-chatbot-header">' +
                '<div class="esco-chatbot-header-avatar">'+avatarHTML+'</div>' +
                '<div class="esco-chatbot-header-info">' +
                    '<div class="esco-chatbot-header-name">'+esc(CFG.bot_name)+'</div>' +
                    '<div class="esco-chatbot-header-status"><i class="fas fa-circle" style="font-size:8px;color:#4caf50;margin-inline-end:4px"></i>'+onlineText+'</div>' +
                '</div>' +
                '<div class="esco-chatbot-header-actions">' +
                    '<button class="esco-chatbot-header-btn" id="escoChatNew" title="'+(isAr?'محادثة جديدة':'New chat')+'"><i class="fas fa-plus"></i></button>' +
                    '<button class="esco-chatbot-header-btn" id="escoChatClose" title="'+(isAr?'إغلاق':'Close')+'"><i class="fas fa-chevron-down"></i></button>' +
                '</div>' +
            '</div>' +
            '<div class="esco-chatbot-messages" id="escoChatMessages"></div>' +
            '<div class="esco-chatbot-input-area">' +
                (CFG.voice_input_enabled ? '<button class="esco-chatbot-voice-btn" id="escoChatVoice" title="'+(isAr?'إدخال صوتي':'Voice input')+'"><i class="fas fa-microphone"></i></button>' : '') +
                '<input type="text" class="esco-chatbot-input" id="escoChatInput" placeholder="'+placeholderText+'" maxlength="2000" autocomplete="off">' +
                '<button class="esco-chatbot-send-btn" id="escoChatSend"><i class="fas fa-paper-plane"></i></button>' +
            '</div>' +
            '<div class="esco-chatbot-powered">Powered by AI</div>' +
        '</div>';

    // Elements
    var bubble = document.getElementById('escoChatBubble');
    var chatWindow = document.getElementById('escoChatWindow');
    var messagesEl = document.getElementById('escoChatMessages');
    var inputEl = document.getElementById('escoChatInput');
    var sendBtn = document.getElementById('escoChatSend');
    var closeBtn = document.getElementById('escoChatClose');
    var newBtn = document.getElementById('escoChatNew');

    // Toggle
    bubble.addEventListener('click', function(){ toggleChat(); });
    closeBtn.addEventListener('click', function(){ toggleChat(false); });

    function toggleChat(forceState){
        isOpen = (forceState !== undefined) ? forceState : !isOpen;
        chatWindow.classList.toggle('open', isOpen);
        bubble.classList.toggle('active', isOpen);
        if(isOpen && messagesEl.children.length === 0) {
            showWelcome();
        }
        if(isOpen) inputEl.focus();
    }

    // New conversation
    newBtn.addEventListener('click', function(){
        conversationId = null;
        messagesEl.innerHTML = '';
        showWelcome();
        fetch('/api/chatbot/new/', {
            method: 'POST',
            headers: {'X-CSRFToken': CFG.csrf_token, 'Content-Type':'application/json'},
            credentials: 'same-origin',
            body: '{}'
        });
    });

    // Send message
    sendBtn.addEventListener('click', function(){ sendMessage(); });
    inputEl.addEventListener('keydown', function(e){
        if(e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); sendMessage(); }
    });

    function sendMessage(text){
        var msg = text || inputEl.value.trim();
        if(!msg || isSending) return;
        inputEl.value = '';
        addMessage('user', msg);
        isSending = true;
        sendBtn.disabled = true;
        showTyping();

        fetch('/api/chatbot/stream/', {
            method: 'POST',
            headers: {'X-CSRFToken': CFG.csrf_token, 'Content-Type':'application/json'},
            credentials: 'same-origin',
            body: JSON.stringify({
                message: msg,
                conversation_id: conversationId,
                page_url: window.location.href
            })
        })
        .then(function(r){
            var ct = r.headers.get('content-type') || '';
            if(ct.indexOf('text/event-stream') === -1){
                return r.json().then(function(data){
                    hideTyping();
                    if(data.error){
                        addMessage('assistant', data.error);
                    } else {
                        if(data.conversation_id) conversationId = data.conversation_id;
                        addMessage('assistant', data.message, data.rich_content, data.quick_replies);
                    }
                    isSending = false;
                    sendBtn.disabled = false;
                    inputEl.focus();
                });
            }

            hideTyping();
            var streamBubble = createStreamBubble();
            var fullText = '';
            var reader = r.body.getReader();
            var decoder = new TextDecoder('utf-8');
            var buffer = '';

            function pump(){
                return reader.read().then(function(result){
                    if(result.done){
                        finishStream(streamBubble, fullText);
                        return;
                    }
                    buffer += decoder.decode(result.value, {stream: true});
                    var lines = buffer.split('\n');
                    buffer = lines.pop();
                    for(var i = 0; i < lines.length; i++){
                        var line = lines[i].trim();
                        if(line.indexOf('data: ') !== 0) continue;
                        try{
                            var evt = JSON.parse(line.substring(6));
                            if(evt.token){
                                fullText += evt.token;
                                streamBubble.innerHTML = formatBubbleHTML(fullText);
                                scrollToBottom();
                            }
                            if(evt.done){
                                if(evt.conversation_id) conversationId = evt.conversation_id;
                                finishStreamParsed(streamBubble, evt.parsed);
                                return;
                            }
                        } catch(e){}
                    }
                    return pump();
                });
            }
            return pump();
        })
        .catch(function(){
            hideTyping();
            addMessage('assistant', isAr ? 'عذراً، حدث خطأ. حاول مرة أخرى.' : 'Sorry, an error occurred. Please try again.');
        })
        .finally(function(){
            isSending = false;
            sendBtn.disabled = false;
            inputEl.focus();
        });
    }

    function createStreamBubble(){
        var msgDiv = document.createElement('div');
        msgDiv.className = 'esco-chatbot-msg assistant';
        var avatarDiv = document.createElement('div');
        avatarDiv.className = 'esco-chatbot-msg-avatar';
        avatarDiv.innerHTML = avatarHTML;
        var bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'esco-chatbot-msg-bubble streaming';
        bubbleDiv.dir = 'auto';
        msgDiv.appendChild(avatarDiv);
        msgDiv.appendChild(bubbleDiv);
        messagesEl.appendChild(msgDiv);
        scrollToBottom();
        return bubbleDiv;
    }

    function finishStreamParsed(bubbleDiv, parsed){
        bubbleDiv.classList.remove('streaming');
        if(!parsed) return;
        bubbleDiv.innerHTML = formatBubbleHTML(parsed.text || '');
        if(parsed.rich_content && parsed.rich_content.type){
            if(parsed.rich_content.type === 'product_cards' && parsed.rich_content.products){
                messagesEl.appendChild(renderProductCards(parsed.rich_content.products));
            }
            if(parsed.rich_content.type === 'comparison' && parsed.rich_content.products){
                var compWrap = document.createElement('div');
                compWrap.className = 'esco-chatbot-msg assistant';
                compWrap.style.maxWidth = '100%';
                var compAvatar = document.createElement('div');
                compAvatar.className = 'esco-chatbot-msg-avatar';
                compAvatar.innerHTML = avatarHTML;
                compWrap.appendChild(compAvatar);
                compWrap.appendChild(renderComparison(parsed.rich_content.products));
                messagesEl.appendChild(compWrap);
            }
        }
        if(parsed.quick_replies && parsed.quick_replies.length){
            messagesEl.appendChild(renderQuickReplies(parsed.quick_replies));
        }
        if(CFG.voice_output_enabled && parsed.text){
            addSpeakerButton(bubbleDiv, parsed.text);
            if(CFG.auto_play_voice) speakText(parsed.text, bubbleDiv);
        }
        scrollToBottom();
    }

    function finishStream(bubbleDiv, fullText){
        bubbleDiv.classList.remove('streaming');
        bubbleDiv.innerHTML = formatBubbleHTML(fullText);
        scrollToBottom();
    }

    function addMessage(role, text, richContent, quickReplies){
        var msgDiv = document.createElement('div');
        msgDiv.className = 'esco-chatbot-msg ' + role;

        var avatarDiv = document.createElement('div');
        avatarDiv.className = 'esco-chatbot-msg-avatar';
        avatarDiv.innerHTML = role === 'assistant' ? avatarHTML : '<i class="fas fa-user"></i>';

        var bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'esco-chatbot-msg-bubble';
        bubbleDiv.dir = 'auto';
        if(role === 'assistant'){
            bubbleDiv.innerHTML = formatBubbleHTML(text);
        } else {
            bubbleDiv.textContent = text;
        }

        msgDiv.appendChild(avatarDiv);
        msgDiv.appendChild(bubbleDiv);
        messagesEl.appendChild(msgDiv);

        // Rich content
        if(richContent && richContent.type){
            if(richContent.type === 'product_cards' && richContent.products){
                messagesEl.appendChild(renderProductCards(richContent.products));
            }
            if(richContent.type === 'comparison' && richContent.products){
                var compWrap = document.createElement('div');
                compWrap.className = 'esco-chatbot-msg assistant';
                compWrap.style.maxWidth = '100%';
                var compAvatar = document.createElement('div');
                compAvatar.className = 'esco-chatbot-msg-avatar';
                compAvatar.innerHTML = avatarHTML;
                compWrap.appendChild(compAvatar);
                compWrap.appendChild(renderComparison(richContent.products));
                messagesEl.appendChild(compWrap);
            }
        }

        // Quick replies
        if(quickReplies && quickReplies.length){
            messagesEl.appendChild(renderQuickReplies(quickReplies));
        }

        // Voice output
        if(role === 'assistant' && CFG.voice_output_enabled && text){
            addSpeakerButton(bubbleDiv, text);
            if(CFG.auto_play_voice) speakText(text, bubbleDiv);
        }

        scrollToBottom();
    }

    function renderProductCards(products){
        var container = document.createElement('div');
        container.className = 'esco-chatbot-products';
        products.forEach(function(p){
            var card = document.createElement('div');
            card.className = 'esco-chatbot-product-card';
            card.onclick = function(){ window.open(p.url, '_blank'); };

            var showPrice = p.show_price !== false;
            var priceHTML = '';
            if(showPrice && p.price){
                priceHTML = '<span class="current-price">' + p.price + ' JOD</span>';
                if(p.has_discount && p.compare_price){
                    priceHTML += ' <span class="old-price">' + p.compare_price + ' JOD</span>';
                }
            }

            var discountBadge = '';
            if(showPrice && p.has_discount && p.discount_percentage){
                discountBadge = '<span class="esco-chatbot-discount-badge">-' + p.discount_percentage + '%</span>';
            }

            var stockHTML = '';
            if(p.in_stock !== undefined){
                if(p.in_stock){
                    stockHTML = '<span class="esco-chatbot-stock in">' + (isAr ? 'متوفر' : 'In Stock') + '</span>';
                } else {
                    stockHTML = '<span class="esco-chatbot-stock out">' + (isAr ? 'غير متوفر' : 'Out of Stock') + '</span>';
                }
            }

            var descHTML = '';
            if(p.short_description){
                descHTML = '<div class="esco-chatbot-product-card-desc">' + esc(p.short_description) + '</div>';
            }

            var nameStr = isAr ? p.name : (p.name_en || p.name);

            card.innerHTML =
                '<div class="esco-chatbot-product-card-img-wrap">' +
                    '<img class="esco-chatbot-product-card-img" src="'+(p.image_url || '/static/images/no-image.svg')+'" alt="'+esc(nameStr)+'" loading="lazy">' +
                    discountBadge +
                '</div>' +
                '<div class="esco-chatbot-product-card-body">' +
                    '<div class="esco-chatbot-product-card-name">' + esc(nameStr) + '</div>' +
                    descHTML +
                    (priceHTML ? '<div class="esco-chatbot-product-card-price">' + priceHTML + '</div>' : '') +
                    '<div class="esco-chatbot-product-card-meta">' +
                        (p.brand ? '<span class="esco-chatbot-product-card-brand">' + esc(p.brand) + '</span>' : '') +
                        stockHTML +
                    '</div>' +
                '</div>' +
                '<a class="esco-chatbot-product-card-btn" href="'+p.url+'" target="_blank" onclick="event.stopPropagation()">' + viewProductText + '</a>';
            container.appendChild(card);
        });
        return container;
    }

    function renderComparison(products){
        var wrapper = document.createElement('div');
        wrapper.className = 'esco-chatbot-comparison';

        products.forEach(function(p, idx){
            var nameStr = isAr ? p.name : (p.name_en || p.name);
            var stockClass = p.in_stock ? 'in' : 'out';
            var stockText = p.in_stock ? (isAr ? 'متوفر' : 'In Stock') : (isAr ? 'غير متوفر' : 'Out of Stock');
            var brandText = p.brand ? (isAr ? 'العلامة: ' : 'Brand: ') + esc(p.brand) : '';
            var catText = p.category ? (isAr ? 'الفئة: ' : 'Category: ') + esc(p.category) : '';
            var meta = [brandText, catText].filter(Boolean).join(' · ');
            var showPrice = p.show_price !== false;
            var priceHTML = (showPrice && p.price) ? '<div class="comp-card-price">' + p.price + ' JOD</div>' : '';

            var card = document.createElement('div');
            card.className = 'comp-card';
            card.innerHTML =
                '<div class="comp-card-header">' + (idx + 1) + '. ' + esc(nameStr) + '</div>' +
                '<div class="comp-card-body">' +
                    '<img class="comp-card-img" src="' + (p.image_url || '/static/images/no-image.svg') + '" alt="">' +
                    '<div class="comp-card-info">' +
                        priceHTML +
                        (meta ? '<div class="comp-card-meta">' + meta + '</div>' : '') +
                        '<div class="comp-card-stock ' + stockClass + '">' + stockText + '</div>' +
                    '</div>' +
                '</div>' +
                '<a class="comp-card-link" href="' + p.url + '" target="_blank">' + viewProductText + '</a>';
            wrapper.appendChild(card);
        });

        return wrapper;
    }

    function renderQuickReplies(replies){
        var container = document.createElement('div');
        container.className = 'esco-chatbot-quick-replies';
        replies.forEach(function(r){
            var btn = document.createElement('button');
            btn.className = 'esco-chatbot-quick-reply';
            btn.dir = 'auto';
            btn.textContent = r.text;
            btn.addEventListener('click', function(){
                container.remove();
                if(r.action === 'compare' && r.data){
                    sendCompareRequest(r.data);
                } else if(r.action === 'lead_form'){
                    showLeadForm();
                } else {
                    sendMessage(r.data || r.text);
                }
            });
            container.appendChild(btn);
        });

        var leadBtn = document.createElement('button');
        leadBtn.className = 'esco-chatbot-quick-reply lead-reply';
        leadBtn.innerHTML = '<i class="fas fa-phone-alt" style="margin-inline-end:4px"></i>' + (isAr ? 'تواصل مع المبيعات' : 'Contact Sales');
        leadBtn.addEventListener('click', function(){
            container.remove();
            showLeadForm();
        });
        container.appendChild(leadBtn);

        return container;
    }

    // ====== Lead Collection Form ======
    var leadFormData = {};

    function showLeadForm(){
        addMessage('assistant', isAr
            ? 'سأساعدك بالتواصل مع فريق المبيعات. أحتاج بعض المعلومات البسيطة:'
            : "I'll help connect you with our sales team. I need some basic information:");

        var formDiv = document.createElement('div');
        formDiv.className = 'esco-chatbot-lead-form';
        formDiv.innerHTML =
            '<div class="lead-form-field">' +
                '<label>' + (isAr ? 'الاسم الكامل *' : 'Full Name *') + '</label>' +
                '<input type="text" id="leadName" placeholder="' + (isAr ? 'أدخل اسمك' : 'Enter your name') + '" required>' +
            '</div>' +
            '<div class="lead-form-field">' +
                '<label>' + (isAr ? 'رقم الهاتف *' : 'Phone Number *') + '</label>' +
                '<input type="tel" id="leadPhone" placeholder="' + (isAr ? '07xxxxxxxx' : '07xxxxxxxx') + '" dir="ltr" required>' +
            '</div>' +
            '<div class="lead-form-field">' +
                '<label>' + (isAr ? 'العنوان *' : 'Address *') + '</label>' +
                '<textarea id="leadAddress" rows="2" placeholder="' + (isAr ? 'المدينة / المنطقة / الشارع - لترتيب التوصيل' : 'City / Area / Street - for delivery arrangement') + '" required></textarea>' +
            '</div>' +
            '<div class="lead-form-field">' +
                '<label>' + (isAr ? 'التاريخ المتوقع للاستلام' : 'Expected Delivery Date') + '</label>' +
                '<input type="text" id="leadDate" placeholder="' + (isAr ? 'مثال: خلال أسبوع' : 'e.g. within a week') + '">' +
            '</div>' +
            '<div class="lead-form-field">' +
                '<label>' + (isAr ? 'المنتج أو الخدمة المطلوبة' : 'Product or Service Needed') + '</label>' +
                '<input type="text" id="leadProduct" placeholder="' + (isAr ? 'ما الذي تبحث عنه؟' : 'What are you looking for?') + '">' +
            '</div>' +
            '<button class="lead-form-submit" id="leadSubmitBtn">' +
                '<i class="fas fa-paper-plane" style="margin-inline-end:4px"></i>' +
                (isAr ? 'إرسال الطلب' : 'Submit Request') +
            '</button>';

        messagesEl.appendChild(formDiv);
        scrollToBottom();

        document.getElementById('leadSubmitBtn').addEventListener('click', function(){
            submitLeadForm(formDiv);
        });
    }

    function submitLeadForm(formDiv){
        var name = document.getElementById('leadName').value.trim();
        var phone = document.getElementById('leadPhone').value.trim();
        var address = document.getElementById('leadAddress').value.trim();
        var date = document.getElementById('leadDate').value.trim();
        var product = document.getElementById('leadProduct').value.trim();

        if(!name || !phone || !address){
            var errMsg = isAr ? 'يرجى إدخال الاسم ورقم الهاتف والعنوان على الأقل.' : 'Please enter at least your name, phone number, and address.';
            var errEl = formDiv.querySelector('.lead-form-error');
            if(!errEl){
                errEl = document.createElement('div');
                errEl.className = 'lead-form-error';
                formDiv.appendChild(errEl);
            }
            errEl.textContent = errMsg;
            return;
        }

        var submitBtn = document.getElementById('leadSubmitBtn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + (isAr ? 'جاري الإرسال...' : 'Submitting...');

        fetch('/api/chatbot/lead-request/', {
            method: 'POST',
            headers: {'X-CSRFToken': CFG.csrf_token, 'Content-Type':'application/json'},
            credentials: 'same-origin',
            body: JSON.stringify({
                customer_name: name,
                customer_phone: phone,
                customer_address: address,
                expected_date: date,
                product_interest: product,
                conversation_id: conversationId,
                page_url: window.location.href
            })
        })
        .then(function(r){ return r.json(); })
        .then(function(data){
            formDiv.remove();
            if(data.success){
                addMessage('assistant', data.message);
            } else {
                addMessage('assistant', data.error || (isAr ? 'حدث خطأ. حاول مرة أخرى.' : 'An error occurred. Please try again.'));
            }
        })
        .catch(function(){
            formDiv.remove();
            addMessage('assistant', isAr ? 'عذراً، حدث خطأ. حاول مرة أخرى.' : 'Sorry, an error occurred. Please try again.');
        });
    }

    function sendCompareRequest(idsStr){
        var ids = idsStr.split(',').map(Number);
        showTyping();
        isSending = true;
        fetch('/api/chatbot/compare/', {
            method: 'POST',
            headers: {'X-CSRFToken': CFG.csrf_token, 'Content-Type':'application/json'},
            credentials: 'same-origin',
            body: JSON.stringify({product_ids: ids})
        })
        .then(function(r){
            if(!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function(data){
            hideTyping();
            if(data.products && data.products.length){
                var msgDiv = document.createElement('div');
                msgDiv.className = 'esco-chatbot-msg assistant';
                var av = document.createElement('div');
                av.className = 'esco-chatbot-msg-avatar';
                av.innerHTML = avatarHTML;
                var bb = document.createElement('div');
                bb.className = 'esco-chatbot-msg-bubble';
                bb.dir = 'auto';
                bb.innerHTML = formatBubbleHTML(isAr ? 'إليك مقارنة بين المنتجات:' : 'Here is a comparison of the products:');
                msgDiv.appendChild(av);
                msgDiv.appendChild(bb);
                messagesEl.appendChild(msgDiv);
                messagesEl.appendChild(renderComparison(data.products));
                scrollToBottom();
            } else {
                addMessage('assistant', isAr ? 'عذراً، لم يتم العثور على المنتجات للمقارنة.' : 'Sorry, products not found for comparison.');
            }
        })
        .catch(function(e){
            hideTyping();
            addMessage('assistant', (isAr ? 'عذراً، لم أتمكن من تحميل المقارنة: ' : 'Sorry, could not load the comparison: ') + e.message);
        })
        .finally(function(){ isSending = false; });
    }

    function showWelcome(){
        // Welcome message
        addMessage('assistant', CFG.welcome_message);

        // Suggested questions
        var suggestions = CFG.suggested_questions || [];
        if(suggestions.length > 0){
            var container = document.createElement('div');
            container.className = 'esco-chatbot-suggestions';
            suggestions.forEach(function(s){
                var btn = document.createElement('button');
                btn.className = 'esco-chatbot-suggestion';
                btn.innerHTML = '<i class="'+(s.icon || 'fas fa-question-circle')+'"></i> <span>'+esc(s.text)+'</span>';
                btn.addEventListener('click', function(){
                    container.remove();
                    sendMessage(s.text);
                });
                container.appendChild(btn);
            });
            messagesEl.appendChild(container);
        }
        scrollToBottom();
    }

    function showTyping(){
        var existing = document.getElementById('escoChatTyping');
        if(existing) return;
        var div = document.createElement('div');
        div.id = 'escoChatTyping';
        div.className = 'esco-chatbot-msg assistant';
        div.innerHTML =
            '<div class="esco-chatbot-msg-avatar">'+avatarHTML+'</div>' +
            '<div class="esco-chatbot-msg-bubble"><div class="esco-chatbot-typing"><span></span><span></span><span></span></div></div>';
        messagesEl.appendChild(div);
        scrollToBottom();
    }

    function hideTyping(){
        var el = document.getElementById('escoChatTyping');
        if(el) el.remove();
    }

    function scrollToBottom(){
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function esc(str){
        if(!str) return '';
        var d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    function formatBubbleHTML(text){
        if(!text) return '';
        var safe = esc(text);
        var lines = safe.split('\n');
        var out = [];
        var listItems = [];
        var listType = '';

        function flushList(){
            if(!listItems.length) return;
            var tag = listType === 'ol' ? 'ol' : 'ul';
            out.push('<' + tag + ' class="chatbot-list">');
            for(var j = 0; j < listItems.length; j++) out.push('<li>' + listItems[j] + '</li>');
            out.push('</' + tag + '>');
            listItems = [];
            listType = '';
        }

        for(var i = 0; i < lines.length; i++){
            var line = lines[i].trim();
            var numMatch = line.match(/^(\d+)[.)\-]\s+(.+)/);
            var bulletMatch = !numMatch && line.match(/^[-•]\s+(.+)/);

            if(numMatch){
                if(listType && listType !== 'ol') flushList();
                listType = 'ol';
                listItems.push(numMatch[2]);
            } else if(bulletMatch){
                if(listType && listType !== 'ul') flushList();
                listType = 'ul';
                listItems.push(bulletMatch[1]);
            } else {
                flushList();
                if(line === ''){
                    out.push('<br>');
                } else {
                    out.push('<p class="chatbot-p">' + line + '</p>');
                }
            }
        }
        flushList();
        return out.join('');
    }

    // ====== Voice Input (STT) ======
    var voiceBtn = document.getElementById('escoChatVoice');
    if(voiceBtn && CFG.voice_input_enabled){
        voiceBtn.addEventListener('click', function(){
            if(isRecording){
                stopRecording();
            } else {
                startRecording();
            }
        });
    }

    function startRecording(){
        if(CFG.voice_provider === 'browser'){
            startBrowserSTT();
        } else {
            startMediaRecording();
        }
    }

    function stopRecording(){
        if(CFG.voice_provider === 'browser'){
            stopBrowserSTT();
        } else {
            stopMediaRecording();
        }
    }

    // Browser Web Speech API (free)
    var recognition = null;
    function startBrowserSTT(){
        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if(!SpeechRecognition){
            addMessage('assistant', isAr ? 'متصفحك لا يدعم الإدخال الصوتي. استخدم Chrome.' : 'Your browser does not support voice input. Use Chrome.');
            return;
        }
        recognition = new SpeechRecognition();
        recognition.lang = CFG.voice_language || 'ar-SA';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = function(){
            isRecording = true;
            voiceBtn.classList.add('recording');
            voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
        };
        recognition.onresult = function(event){
            var text = event.results[0][0].transcript;
            if(text.trim()){
                inputEl.value = text;
                sendMessage();
            }
        };
        recognition.onerror = function(event){
            isRecording = false;
            voiceBtn.classList.remove('recording');
            voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
            if(event.error !== 'no-speech' && event.error !== 'aborted'){
                addMessage('assistant', isAr ? 'خطأ في التعرف على الصوت. حاول مرة أخرى.' : 'Voice recognition error. Please try again.');
            }
        };
        recognition.onend = function(){
            isRecording = false;
            voiceBtn.classList.remove('recording');
            voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        };
        recognition.start();
    }

    function stopBrowserSTT(){
        if(recognition){
            recognition.stop();
        }
        isRecording = false;
        voiceBtn.classList.remove('recording');
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    }

    // Server-side STT (paid providers)
    function startMediaRecording(){
        navigator.mediaDevices.getUserMedia({audio: true})
        .then(function(stream){
            audioChunks = [];
            mediaRecorder = new MediaRecorder(stream, {mimeType: 'audio/webm;codecs=opus'});
            mediaRecorder.ondataavailable = function(e){
                if(e.data.size > 0) audioChunks.push(e.data);
            };
            mediaRecorder.onstop = function(){
                stream.getTracks().forEach(function(t){ t.stop(); });
                var blob = new Blob(audioChunks, {type: 'audio/webm'});
                sendAudioToServer(blob);
            };
            mediaRecorder.start();
            isRecording = true;
            voiceBtn.classList.add('recording');
            voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
        })
        .catch(function(){
            addMessage('assistant', isAr ? 'لم يتم السماح بالوصول للمايكروفون.' : 'Microphone access was denied.');
        });
    }

    function stopMediaRecording(){
        if(mediaRecorder && mediaRecorder.state === 'recording'){
            mediaRecorder.stop();
        }
        isRecording = false;
        voiceBtn.classList.remove('recording');
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    }

    function sendAudioToServer(blob){
        var formData = new FormData();
        formData.append('audio', blob, 'recording.webm');
        showTyping();
        fetch('/api/chatbot/voice/transcribe/', {
            method: 'POST',
            headers: {'X-CSRFToken': CFG.csrf_token},
            credentials: 'same-origin',
            body: formData
        })
        .then(function(r){ return r.json(); })
        .then(function(data){
            hideTyping();
            if(data.text){
                inputEl.value = data.text;
                sendMessage();
            } else if(data.error){
                addMessage('assistant', data.error);
            }
        })
        .catch(function(){
            hideTyping();
            addMessage('assistant', isAr ? 'خطأ في معالجة الصوت.' : 'Error processing audio.');
        });
    }

    // ====== Voice Output (TTS) ======
    function speakText(text, bubbleEl){
        if(!CFG.voice_output_enabled || !text) return;
        if(CFG.voice_provider === 'browser'){
            speakBrowserTTS(text);
        } else {
            speakServerTTS(text, bubbleEl);
        }
    }

    function speakBrowserTTS(text){
        if(!window.speechSynthesis) return;
        window.speechSynthesis.cancel();
        var utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = CFG.voice_language || 'ar-SA';
        var voices = window.speechSynthesis.getVoices();
        var lang = (CFG.voice_language || 'ar-SA').substring(0, 2);
        for(var i = 0; i < voices.length; i++){
            if(voices[i].lang.indexOf(lang) === 0){
                utterance.voice = voices[i];
                break;
            }
        }
        window.speechSynthesis.speak(utterance);
    }

    function speakServerTTS(text, bubbleEl){
        fetch('/api/chatbot/voice/synthesize/', {
            method: 'POST',
            headers: {'X-CSRFToken': CFG.csrf_token, 'Content-Type': 'application/json'},
            credentials: 'same-origin',
            body: JSON.stringify({text: text})
        })
        .then(function(r){
            if(!r.ok) throw new Error('TTS failed');
            return r.blob();
        })
        .then(function(blob){
            var url = URL.createObjectURL(blob);
            var audio = new Audio(url);
            audio.onended = function(){ URL.revokeObjectURL(url); };
            audio.play();
        })
        .catch(function(){});
    }

    // Add speaker button to assistant messages
    function addSpeakerButton(bubbleDiv, text){
        if(!CFG.voice_output_enabled) return;
        var btn = document.createElement('button');
        btn.className = 'esco-chatbot-speak-btn';
        btn.title = isAr ? 'استمع' : 'Listen';
        btn.innerHTML = '<i class="fas fa-volume-up"></i>';
        btn.addEventListener('click', function(e){
            e.stopPropagation();
            speakText(text, bubbleDiv);
        });
        bubbleDiv.appendChild(btn);
    }

})();
