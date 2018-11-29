<?php

namespace ThoughtBundle\Service;

use FOS\UserBundle\Model\User;
use Symfony\Component\DependencyInjection\Container;
use Symfony\Component\HttpFoundation\Cookie;
use Symfony\Component\HttpFoundation\Response;

/**
 * Class Search
 * @package ThoughtBundle\Service
 */
class Search
{
    /**
     * @var Container
     */
    private $container;

    /**
     * Search constructor.
     * @param Container $container
     */
    public function __construct(Container $container)
    {
        $this->container = $container;
    }

    /**
     * @param array|null $searchParams
     * @return mixed
     * @throws \Exception
     */
    public function preSearch($searchParams)
    {
        if ($searchParams) {
            if (!$this->container->get('security.context')->getToken()->getUser() instanceof User) {
                $request = $this->container->get('request');

                $countSearch = $request->cookies->get('countSearch', 0) + 1;

                $cookie = new Cookie('countSearch', $countSearch);
                $response = new Response();
                $response->headers->setCookie($cookie);
                $response->sendHeaders();

//                if ($countSearch > $this->container->getParameter('quantity_search')) {
//                    $searchParams = null;
//
//                    $request->getSession()
//                        ->getFlashBag()
//                        ->add('success', $this->container->get('translator')->trans('user.search.need_logged', array(
//                            '%quantity_search%' => $this->container->getParameter('quantity_search'),
//                        )))
//                    ;
//                }
            }
        }

        return $searchParams;
    }
}
