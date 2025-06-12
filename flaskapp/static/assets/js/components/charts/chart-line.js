'use strict';

//
// Sales chart
//

var SalesChart = (function() {

  // Variables

  var $chart = $('#chart-users-last-6-months');


  // Methods

  function init($chart) {

    // Print usersLast6Months 
    console.log(usersLast6Months);
    console.log(labels);


    var salesChart = new Chart($chart, {
      type: 'line',
      options: {
        scales: {
          yAxes: [{
            gridLines: {
              lineWidth: 1,
              color: Charts.colors.gray[900],
              zeroLineColor: Charts.colors.gray[900]
            },
            ticks: {
              callback: function(value) {
                if (!(value % 10)) {
                  return value;
                }
              }
            }
          }]
        },
        tooltips: {
          callbacks: {
            label: function(item, data) {
              var label = data.datasets[item.datasetIndex].label || '';
              var yLabel = item.yLabel;
              var content = '';

              if (data.datasets.length > 1) {
                content += label + ': ';
              }

              content += ' ' + yLabel + ' nuevos usuarios';
              return content;
            }
          }
        }
      },
      data: {
        labels: typeof labels !== 'undefined' ? labels : [],
        datasets: [{
          label: 'Usuarios/Meses',
          data: typeof usersLast6Months !== 'undefined' ? usersLast6Months : []
        }]
      }
    });

    // Save to jQuery object

    $chart.data('chart', salesChart);

  };


  // Events

  if ($chart.length) {
    init($chart);
  }

})();
