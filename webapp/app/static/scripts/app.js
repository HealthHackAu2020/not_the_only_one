// namespace
window.semantic = {
    handler: {}
  };

semantic.home = {};

// ready event
semantic.home.ready = function() {

  if($(window).width() > 600) {
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
  
};

$(document)
  .ready(semantic.home.ready)
;
