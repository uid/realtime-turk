var
	server = 'http://crowdy.csail.mit.edu/retainer/',
	reservations = [],
	reservationMap = {},
	hitTypes = []
	snowman = '\u2603'

$(init)

function init(){
	setInterval(updateData, 3000)
	initData()
	
	$('#btn-complete-all-resvs').click(onClickMarkAll)
}

function onClickMarkAll(type){
	$.post(server + 'reservation/finish/all', { hitType: typeof type == 'string' ? type : '' }, function(){
		updateData()
	})
}

function updateHITTypes(){
	var types = $.unique($.unique($.map(reservations, function(e){ return e.proto.hitTypeID })))
	if($(types).not(hitTypes).length || $(hitTypes).not(types).length){
		// then the types have changed
		$('.hitType-btn').remove()
		$('#controls').append($.map(types, function(e){ return hitTypeBtn(e) }))
		hitTypes = types
	}
}

function hitTypeBtn(type){
	return $('<input />', {
		type: 'button',
		class: 'span2 hitType-btn',
		value: type,
		click: function(e){
			onClickMarkAll(type)
		}
	})
}

function initData(){
	initReservations()
}

function updateData(){
	updateReservations()
}

function initReservations(){
	$.get(server + 'reservation/list', onReservationsInit)
}

function updateReservations(){
	$.get(server + 'reservation/list', onReservationsUpdate)
}

function onReservationsInit(data){
	data = JSON.parse(data).reverse()
	if(!(data instanceof Array)) throw 'retainer server down'
	addReservations(data)
	updateHITTypes()
}

function onReservationsUpdate(data){
	data = JSON.parse(data).reverse()
	if(!(data instanceof Array)) alert('retainer connection lost')
	
	currentReservations = data
	cmp = compareReservations(reservations, currentReservations)
	
	if(cmp.added.length > 0) addReservations(cmp.added)
	if(cmp.deleted.length > 0) removeReservations(cmp.deleted)
	if(cmp.modified.length > 0) modifyReservations(cmp.modified)
	
	updateHITTypes()
}

function addReservations(resvs){
	for(var i = 0; i < resvs.length; ++i){
		addReservation(resvs[i])
		reservations.unshift(resvs[i])
	}
}

function removeReservations(resvs){
	for(var i = 0; i < resvs.length; ++i){
		removeReservation(resvs[i])
		reservations.splice(reservations.indexOf(resvs[i]), 1)
	}
}

function removeReservation(resv){
	var elem = resvElem(resv)
	delete reservationMap[hash(resv)]
	elem.remove() // may want to do an animation
}

function modifyReservations(resvs){
	for(var i = 0; i < resvs.length; ++i){
		var old = resvs[i].old
		var current = resvs[i].current
		
		var oldElem = resvElem(old)
		var newElem = htmlReservation(current)
		$(oldElem).replaceWith(newElem)
		delete reservationMap[hash(old)]
		reservationMap[hash(current)] = current
		
		reservations.splice(reservations.indexOf(old), 1, current)
		
		// animate
		forceCSS(newElem[0], 'color')
		newElem.removeClass('X-hidden')
	}
}

function addReservation(r){
	var li = htmlReservation(r)
	$('#reservations').prepend(li)
	reservationMap[hash(r)] = r
	forceCSS(li[0], 'opacity')
	li.removeClass('X-hidden')
}

function htmlReservation(r){
	var id = hash(r)
	var li = $('<div />', {
		class: 'row resv-item X-hidden',
		'data-hash': id
	})
	
	var ids = $('<div />', {
		class: 'span2 cell resv-ids',
		text: r.foreignID + ' (' + r.id + ')'
	})
	
	var protoInfo = $('<div />', {
		class: 'span2 cell resv-proto',
		text: r.proto.hitTypeID
	})
	
	var timeLeft = $('<div />', {
		class: 'span3 cell resv-time',
		text: new Date(r.startTime).toString().replace(/GMT.*/, '').substring(4)
	})
	
	var assignments = $('<div />', {
		class: 'span2 cell resv-assignments',
		text: snowman.times(r.workers) + ' / ' + r.assignments
	})
	
	var invoked = $('<div />', {
		class: 'span1 cell bool resv-invoked'
	}).click(function(e){
		r.invoked ? null : invokeReservation(r)
	}).append($('<input />', { 
		type: 'button', value: 'Invoke' + (r.invoked ? 'd' : ' '), disabled: r.invoked
	}))
	
	var done = $('<div />', {
		class: 'span2 cell bool resv-done',
		text: 'Complete?: '
	}).append($('<input />', { type: 'checkbox', checked: r.done } ))
	.click(function(e){
		r.done ? 
			unfinishReservation(r) :
			finishReservation(r)
	})
	
	li.append(ids, protoInfo, timeLeft, assignments, invoked, done)
	return li
}

function finishReservation(r){
	$.post(server + 'reservation/finish', {
		id: r.id
	}, updateReservations)
}

function unfinishReservation(r){
	$.post(server + 'reservation/unfinish', {
		id: r.id
	}, updateReservations)
}

function invokeReservation(r){
	$.post(server + 'reservation/invoke', {
			id: r.id
	}, updateReservations)
}

function compareReservations(old, current){
	var ret = {
		modified: [],
		deleted: [],
		added: []
	}
	
	// find additions, modifications
	for(var i = 0; i < current.length; ++i){
		var item = current[i]
		var _has = has(old, item)
		if(!_has){
			ret.added.push(item)
		} else if(_has.id){ // modified
			ret.modified.push({ old: _has, current: item })
		} else { /* identical, no update */ }
	}
	
	// find deletions
	for(i = 0; i < old.length; ++i){
		item = old[i]
		if(!has(current, item)) ret.deleted.push(item)
	}
	
	if(ret.modified.length > 0 || ret.deleted.length > 0 || ret.added.length > 0){
		console.log('cmp', ret)
	}
	return ret
	
	function has(list, resv){
		for(var i = 0; i < list.length; ++i){
			var elem = list[i]
			if(elem.id == resv.id) return hash(elem) == hash(resv) ? true : elem
		}
		return false
	}
}

// Convenience functions.

function resvElem(r){
	return $('div[data-hash="' + hash(r) + '"]')
}

function elemResv($e){
	return reservationMap[$e.attr('data-hash')]
}

String.prototype.times = function(n){
	var ret = ''
	for(var i = 0; i < n; ++i) ret += this
	return ret
}

function hash(obj){
	// ridiculously slow to use SHA3 so often.  guess I shouldn't be surprised
	return /*CryptoJS.SHA3(*/JSON.stringify(obj)/*).toString()*/
}

function forceCSS(elem, prop){
	window.getComputedStyle(elem)[prop]
}