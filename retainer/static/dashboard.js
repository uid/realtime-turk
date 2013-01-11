var 
    BASE = 'http://crowdy.csail.mit.edu:8000/',
    stor = localStorage,
    reservations,
    protos

$(init)

function init(){
    if(!stor.reservations){
        reservations = []
    } else {
        reservations = JSON.parse(stor.reservations)
        refreshReservations()
    }
    $('#resv-new').click(makeReservation)
    
    if(!stor.protos){
        protos = []
    } else {
        protos = JSON.parse(stor.protos)
        refreshProtos()
    }
    $('#proto-new').click(makeProto)
    
    $('.resv-invoke').on('click', onInvoke)
    $('.resv-finish').on('click', onFinish)
    $('.resv-cancel').on('click', onCancel)
}

function onInvoke(e){
    var resv = reservations[$(e.currentTarget).parent().data('index')]
    invokeReservation(resv)
}

function onFinish(e){
    var resv = reservations[$(e.currentTarget).parent().data('index')]
    finishReservation(resv)
}

function onCancel(e){
    var resv = reservations[$(e.currentTarget).parent().data('index')]
    cancelReservation(resv)
}

function makeReservation(){
    console.log('make reservation')
    
    var resv = {
        id: $('#resv-id').val(),
        foreignID: $('#resv-foreignID').val(),
        delay: $('#resv-delay').val(),
        numAssignments: $('#resv-numAssignments').val(),
        payload: $('#resv-payload').val()
    }
    
    postReservation(resv)
    reservations.push(resv)
    refreshReservations()
}

function invokeReservation(resv){
    console.log('invoke', resv)
    $.post(BASE + 'reservation/invoke', {
        id: resv.remoteID
    }, function(data){
        console.log('invoke', data)
        resv.invoked = true
        refreshReservations()
    })
}

function finishReservation(resv){
    console.log('finish', resv)
    $.post(BASE + 'reservation/finish', {
        id: resv.remoteID
    }, function(data){
        console.log('finish', data)
        resv.finished = true
        refreshReservations()
    })
}

function cancelReservation(resv){
    console.log('cancel', resv)
    $.post(BASE + 'reservation/cancel', {
        id: resv.remoteID
    }, function(data){
        console.log('cancel', data)
        resv.cancelled = true
        refreshReservations()
    })
}

function makeProto(){
    console.log('make proto')
    
    var proto = { 
        hit_type_id: 'Dashboard',
        title: 'Dashboard HIT',
        description: 'Dashboard',
        keywords: 'dashboard',
        url: 'http://crowdy.csail.mit.edu:8000/static/test.html',
        frame_height: 1200,
        reward: 0.05,
        assignment_duration: 1200,
        lifetime: 12000,
        max_assignments: 1,
        auto_approval_delay: 60 * 60 * 24,
        approval_rating: 92,
        worker_locale: 'US'
    }
    
    postProto(proto)
    protos.push(proto)
    refreshProtos()
}

function refreshReservations(){
    stor.reservations = JSON.stringify(reservations)
    $('#reservations').children().remove()
    for(var i = 0; i < reservations.length; i++){
        $('#reservations').append('<li data-index="' + i + '">' + reservationButtons() + JSON.stringify(reservations[i]) + '</li>')
    }
}

function refreshProtos(){
    stor.protos = JSON.stringify(protos)
    $('#protos').children().remove()
    for(var i = 0; i < protos.length; i++){
        $('#protos').append('<li data-index="' + i + '">' + JSON.stringify(protos[i]) + '</li>')
    }
}

function reservationButtons(){
    return '\
    <input type="button" class="resv-invoke" value="Invoke" />\
    <input type="button" class="resv-finish" value="Finish" />\
    <input type="button" class="resv-cancel" value="Cancel" />\
    '
}

function postReservation(resv){
    $.post(BASE + 'reservation/make', resv, function(data){
        console.log('new reservation response', data)
        resv.remoteID = parseInt(data)
        refreshReservations()
    })
}

function postProto(proto){
    $.post(BASE + 'puttask', {
        json: JSON.stringify(proto)
    }, function(data){
        console.log('new proto made', data)
        proto.id = parseInt(data)
        refreshProtos()
    })
}