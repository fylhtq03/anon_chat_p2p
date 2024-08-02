$(document).ready(function() {
        var csrfToken = $("meta[name='csrf-token']").attr('content');
        function postMessage() {
          var message = $('#message').val();
          var name = $('#name').val();
          if (message !== '' && name !== '') {
            $.post('/post_message', {message: message, name: name, csrf_token: csrfToken}, function(data) {
              if (data.status === 'OK') {
                $('#message').val('');
              }
            });
          }
        }

        function getMessages() {
          $.get('/get_messages', function(data) {
            $('#chatbox').empty();
            for (var i = 0; i < data.length; i++) {
                var message = data[i];
              var html = '<strong>' + message.name + ' : ' + message.message + '<br>';
              $('#chatbox').append(html);
            }
          });
        }

        setInterval(function() {
          getMessages();
        }, 500);

        $('#sendButton').click(function() {
          postMessage();
        });

        $('#message').keypress(function(e) {
          if (e.which === 13) {
            postMessage();
          }
        });
      });