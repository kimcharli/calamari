'use strict';

var adminApp = angular.module('adminApp', []);
adminApp.config(function($routeProvider) {

    $routeProvider.when('/user', {
        templateUrl: 'views/user.html',
        title: 'User Settings',
        controller: 'UserCtrl'
    }).when('/general', {
        templateUrl: 'views/general.html',
        title: 'General Settings',
        controller: 'GeneralCtrl'
    }).when('/cluster', {
        templateUrl: 'views/cluster.html',
        title: 'Cluster Settings',
        controller: 'ClusterCtrl'
    }).when('/users', {
        templateUrl: 'views/users.html',
        title: 'Users Settings',
        controller: 'UsersCtrl'
    }).otherwise({
        redirectTo: '/user'
    });

});
adminApp.factory('menus', function() {
    return {
        menu: function(active) {
            var labels = ['General', 'Cluster', 'User', 'Users'];
            var url = ['general', 'cluster', 'user', 'users'];
            var res = [];
            for (var i = 0; i < url.length; ++i) {
                res.push({
                    label: labels[i],
                    clazz: url[i] === active ? 'active' : '',
                    url: '#/' + url[i]
                });
            }
            return res;
        }
    };
});
adminApp.run(function($rootScope, $route) {
    $rootScope.$on('$routeChangeSuccess', function() {
        $rootScope.pageTitle = $route.current.title;
    });
});
adminApp.factory('pageTitle', function($rootScope, $route) {
    return {
        update: function() {
            $rootScope.pageTitle = $route.current.title;
        }
    };
});
