<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />
<%namespace file="/spark_base.mako" import="jqs_style, make_sparkline" />
<%namespace file="/sorting_base.mako" import="get_sort_url, get_css" />
<%!
    import re
%>

%if message:
    ${render_msg( message, 'done' )}
%endif

${jqs_style()}
${get_css()}

<!--jobs_per_user.mako-->
<div class="toolForm">
    <div class="toolFormBody">
        <h4 align="center">Jobs Per User</h4>
        <h5 align="center">
            Click User to view details. Graph goes from present to past(${day_limit} days).
        </h5>
        <table align="center" width="60%" class="colored">
            %if len( jobs ) == 0:
                <tr><td colspan="2">There are no jobs.</td></tr>
            %else:
                <tr class="header">
                    <td>
                        ${get_sort_url(sort_id, order, 'user_email', 'jobs', 'per_user', 'User')}
                        <span class='dir_arrow user_email'>${arrow}</span>
                    </td>
                    <td>
                        ${get_sort_url(sort_id, order, 'total_jobs', 'jobs', 'per_user', 'Total Jobs')}
                        <span class='dir_arrow total_jobs'>${arrow}</span>
                    </td>
                </tr>
                <% ctr = 0 %>
                %for job in jobs:
                    <% key = re.sub(r'\W+', '', job[0]) %>
                    %if ctr % 2 == 1:
                        <tr class="odd_row">
                    %else:
                        <tr class="tr">
                    %endif
                        <td><a href="${h.url_for( controller='jobs', action='user_per_month', email=job[0], sort_id='default', order='default' )}">${job[0]}</a></td>
                        <td>${job[1]}</td>
                        ${make_sparkline(key, trends[key], "line", "/ day")}
                        <td id="${key}"></td>
                    </tr>
                    <% ctr += 1 %>
                %endfor
            %endif
        </table>
    </div>
</div>
<!--End jobs_per_user.mako-->
        