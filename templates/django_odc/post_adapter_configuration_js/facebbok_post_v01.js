/**
 * Title: Configuration instructions and examples for posting data to the Facebook Post V01 ODC Post Adapter Source
 * User: mg@metalayer.com
 * Date: 5/30/13
 */

/**
 * Below is an example of the JSON format you should use to encode posts sent to this post adapted.
 * PLEASE NOTE THAT ALL FIELDS ARE REQUIRED
 */
var posts = [
    {
        message: '', //The raw message string
        id: '', //The post id as a string
        created_time: '2013-05-30T20:28:16+0000', //encoded datetime taken directly from facebook
        link: '', //The url of the post in question
        user_id: '', //The id of the user
        user_name: '' //The screen name of the user
    }
];

/**
 * NOTE: YOU MUST BATCH UP THE POSTS YOU SEND TO THIS API, ANYTHING OVER A CALL EVERY COUPLE OF SECONDS
 * IS LIKELY TO BREAK IT!
 */

/**
 * The above posts collection should be posted to the adapter in your favourite language as raw JSON
 */

/**
 * Here is an example using jQuery
 */
$.ajax({
    url:'http://something.com',  // The url you have been provided
    type:"POST",  //The type of request, must be POST
    data:JSON.stringify(posts),  // JSON stringify the posts from above
    contentType:"application/json; charset=utf-8",  // Set the content type like this
    dataType:"json",  // Specify json data type
    success: function(return_data){},
    error:function(jqXHR, status, error){}
});