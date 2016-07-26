$(document).ready(function () {
	
	g_IndicatorCode = $('#indicators_anchor').attr('data-value');
	
	$('.site_menu_link').click(function(e) {
		switch($(e.target).text()){
			
			case 'Contact Me':
				$('.contact_box').css('display','block');
				$('.contact_box').center();
				break;
			
			case 'About':
				$('.about_box').css('display','flex');
				$('.about_box').center();
				break;

			case 'Index Analysis':
				window.location = 'http://lockers.cloudapp.net/index_vs_indicator/EG.USE.PCAP.KG.OE+North America+2000+2012';
				break;
			
			case 'Version':
				break;
		}
	});

	//Initialize About Box with the text associated with the top ab_menu item
	$('.ab_content h1').text( $('#ab_item_1').text() );
	$('#ab_text_1').css('display', 'block');

	$('.ab_menu_item').click(function(e) {
		$('.ab_content h1').text($(this).text());
		var id = $(e.target).attr("id");
		var num = id.slice(-1);   //Get the last character in the string
		$('.ab_text').css('display', 'none');
		$('#ab_text_' + num).css('display', 'block');
	});
	
	$('.home_link').click(function(e) {
		window.location = 'http://lockers.cloudapp.net/';
	});

	$('#contact_box_close').click(function(e) {
		$('.contact_box').css('display', 'none');
	});

	$('.selected_item').click(function(e) {
		var id = $(this).attr("id");
		var setWidth = false;
		if(id.indexOf('year') > -1) {
			setWidth = true
		}

		var idx = id.indexOf('_anchor');
		var list_selector = '#' + id.substring(0, idx);
		$(list_selector).css('display', 'flex');
		putList('#' + id, list_selector, setWidth);
	});


	$('.item').click( function(e) {
		// Get the id of the list container and add '_anchor' to get the id of the div heading the list.
		var clicked_text = $(e.target).text();
		g_IndicatorCode = $(e.target).attr('data-value'); //global
		var id  = $(e.target).parent().attr('id') + '_anchor';
		$('#' + id).text(clicked_text);
	});

	$('.item_list').mouseleave(function(e) {
		$(this).css('display', 'none');
	});


	$('#main_submit').click(function() {
		var sy = $('#start_year').val();
		var ey = $('#end_year').val();
		var region = $('#region_anchor').text();
		if(!validYears(sy, ey)) {
			alert("Please enter valid start and end years");
			return;
		}
		var ia = $('#indicators_anchor').text();
		if(ia == '(select)') {
			alert("Please select a valid indicator from the list");
			return;
		}
		
		if(String(window.location.pathname).indexOf('params') > -1) {
			var params = g_IndicatorCode + '+' + sy + '+' + ey;
			window.location = 'http://lockers.cloudapp.net/params/' + params;
		} 
		else if(String(window.location.pathname).indexOf('index_vs_indicator') > -1) {
			g_IndicatorCode = 'EG.USE.PCAP.KG.OE';
			var params = g_IndicatorCode + '+' + region + '+' + sy + '+' + ey;
			window.location = 'http://lockers.cloudapp.net/index_vs_indicator/' + params;	
		}
		else  {
			var params = g_IndicatorCode + '+' + sy + '+' + ey;
			window.location = 'http://lockers.cloudapp.net/params/' + params;	
		}		
	});

});

function validYears(startYear, endYear) {
	var sy = parseInt(startYear);
	var ey = parseInt(endYear);
	if(isNaN(sy) || isNaN(ey)) return false;
	
	sy = parseInt(startYear);
	ey = parseInt(endYear);
	
	if(sy < 1960 || sy > 2015) return false;
	
	if(ey < 1960 || ey > 2015) return false;

	if(ey <= sy) return false;
		
	return true;
}

function putList(anchor, list, setWidth) {
	var offset = $(anchor).offset();
	var height = $(anchor).outerHeight();
	if(setWidth) {
		$(list + ' div').width($(anchor).width()); 
	}
	$(list).offset({top: offset.top + height, left: offset.left});
}

jQuery.fn.center = function () {
    this.css("position", "fixed");
	this.css("top", Math.max(0, (($(window).height() - $(this).innerHeight()) / 2)));
	this.css("left", Math.max(0, (($(window).width() - $(this).innerWidth()) / 2)));
	return this;
};
