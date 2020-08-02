// base
// Semantic UI breakpoints
var mobileBreakpoint = '824px';
var tabletBreakpoint = '992px';
var smallMonitorBreakpoint = '1200px';

$(document).ready(function () {
  // Enable dismissable flash messages
  $('.message .close').on('click', function () {
    $(this).closest('.message').transition('fade');
  });

  // Enable mobile navigation
  $('#open-nav').on('click', function () {
    $('.mobile.only .vertical.menu').transition('slide down');
  });

  // Enable sortable tables
  $('table.ui.sortable').tablesort();

  // Enable dropdowns
  $('.dropdown').dropdown();
  $('select').dropdown();
  function icontains(elem, text) {
    return (elem.textContent || elem.innerText || $(elem).text() || "")
      .toLowerCase().indexOf((text || "").toLowerCase()) > -1;
  }

  $.expr[':'].icontains = $.expr.createPseudo ?
    $.expr.createPseudo(function (text) {
      return function (elem) {
        return icontains(elem, text);
      };
    }) :
      function (elem, i, match) {
        return icontains(elem, match[3]);
      };
});


// Add a case-insensitive version of jQuery :contains pseduo
// Used in table filtering
(function ($) {
})(jQuery);


// mobile dropdown menu state change 
// This code is used for modeling the state of the mobile dropdown menu. 
// When a mobile menu item with a dropdown is touched, the changeMenu function
// is called. It gets all the children of the dropdown and stores them as the
// children variable. During this time, the state of the dropdown menu is saved
// into the currentState array for later. A 'back' item that has an onclick attr
// calling the back() function is appended to the children variable and the
// html of the mobile dropdown is set to the children variable. 
// If the back button is clicked, we get the parent menu of the submenu by popping
// the currentState variable.

var currentState = [];

function changeMenu(e) {
  var children = $($(e).children()[1]).html();
  children += '<a class="item" onClick="back()">Back</a><i class="back icon"></i>';
  currentState.push($('.mobile.only .vertical.menu').html());
  $('.mobile.only .vertical.menu').html(children);
}

function back() {
  $('.mobile.only .vertical.menu').html(currentState.pop());
}


// namespace
window.semantic = {
    handler: {}
  };

semantic.home = {};

// ready event
semantic.home.ready = function() {

  // if($(window).width() > 600) {
  var path = location.pathname;
  var is_root = path == "/";
  endpoint = path.substr(1);
  if (!isNaN(endpoint)) {
    is_root = true;
  }
  if (is_root) {
    $('body')
      .visibility({
        offset         : -60,
        observeChanges : false,
        once           : false,
        continuous     : false,
        onTopPassed: function() {
          requestAnimationFrame(function() {
            $('.following.bar')
              .addClass('light fixed')
              .find('.menu')
                .removeClass('inverted')
            ;
            $('.following .additional.item')
              .transition('scale in', 750)
            ;
          });
        },
        onTopPassedReverse: function() {
          requestAnimationFrame(function() {
            $('.following.bar')
              .removeClass('light fixed')
              .find('.menu')
                .addClass('inverted')
                .find('.additional.item')
                  .transition('hide')
            ;
          });
        }
      })
    ;
  }
  else {
    $('body')
      .visibility({
        offset         : -10,
        observeChanges : false,
        once           : false,
        continuous     : false,
        onTopPassed: function() {
          requestAnimationFrame(function() {
            $('.following.bar')
              .addClass('light fixed')
              .find('.menu')
                .removeClass('inverted')
            ;
            $('.following .additional.item')
              .transition('scale in', 750)
            ;
          });
        }
      })
    ;
  }
  
};

$(document)
  .ready(semantic.home.ready)
;
