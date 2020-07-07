<?php

namespace ThoughtBundle\Controller;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\EntityManager;
use Doctrine\ORM\OptimisticLockException;
use Exception;
use Knp\Component\Pager\Pagination\PaginationInterface;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Cookie;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use ThoughtBundle\Entity\Banner;
use ThoughtBundle\Entity\Comment;
use ThoughtBundle\Entity\Like;
use ThoughtBundle\Entity\Thought;
use ThoughtBundle\Entity\ThoughtRelated;
use ThoughtBundle\Model\ThoughtModel;
use ThoughtBundle\Model\TopicChainModel;
use ThoughtBundle\Service\Search;

/**
 * Class HomepageController
 *
 * @package ThoughtBundle\Controller
 */
class HomepageController extends Controller
{
    /**
     * @Route("/", methods={"GET"}, options={"sitemap" = true})
     *
     * @param Request $request
     *
     * @return Response
     *
     * @throws Exception
     */
    public function indexAction(Request $request)
    {
        /** @var ThoughtModel $modelThought */
        $modelThought = $this->container->get('thought.model.thought_model');
        /** @var Search $serviceSearch */
        $serviceSearch = $this->container->get('thought.service.search_service');
        /** @var EntityManager $em */
        $em = $this->container->get('doctrine.orm.entity_manager');
        /** @var PaginationInterface $paginator */
        $paginator = $this->get('knp_paginator');
        /** @var TopicChainModel $modelTopicChain */
        $modelTopicChain = $this->container->get("thought.model.topicchain_model");
        $start = microtime(true);

        $page = $request->query->getInt('page', 1);

        if (!$page) {
            $page = 1;
        }
        $countItem = 10;

        $search = $serviceSearch->preSearch($request->get('search'));

        $default = $request->query->get('default');

        $role = User::ROLE_USER;

        if ($this->isGranted(User::ROLE_STUDENT)) {
            $role = User::ROLE_STUDENT;
        }

        $thoughts = $modelThought->getThoughts($search, $default, $role, $page);

        /** @var PaginationInterface|Thought[] $pagination */
        $pagination = $paginator->paginate(
            $thoughts,
            $page,
            $countItem
        );

        $cloud = $modelThought->getCloud($search['field'], $thoughts, $search['words']);

        $comments = [];
        foreach ($pagination as $thought) {
            $comments[$thought->getId()][] = $em->getRepository(Comment::class)->getLastComments($thought);
        }

        $welcomeText = $em->getRepository('ThoughtBundle:Content')->findOneBy([
            'contentType' => 'welcome',
        ]);

        $timeExecute = microtime(true) - $start;

        $collectiveChains = $em->getRepository('ThoughtBundle:Chain')->getAllCollectiveChains($role);
        $dynamicBanners = $em->getRepository(Banner::class)->findAll();

        // Get topics with chains for selector
            $topicsArray = $modelTopicChain->getTopicsWithChains();

            $topicPrivateItem = [];
            if ($this->getUser()) {
                $topicPrivateItem = $modelTopicChain->getUserPrivateChaines($this->getUser());
            }

            $topicsArray[] = $topicPrivateItem;
        //---

        // Array friends for related quotes
            $userFriend = [];
            $user = $this->getUser();

            if ($user) {
                $friends = $this->getDoctrine()->getRepository('ApplicationSonataUserBundle:Friendship')->getFriends($user);
                foreach ($friends as $friend) {
                    if ($friend->getUser() == $user) {
                        $userFriend[$friend->getFriend()->getId()] = $friend->getFriend()->getFirstname();
                    } else {
                        $userFriend[$friend->getUser()->getId()] = $friend->getUser()->getFirstname();
                    }
                }
                $userFriend[$user->getId()] = 'Yours';
            }

        //---

        $response = $this->render('ThoughtBundle::homepage.html.twig', [
            'thoughts'    => $pagination,
            'comments'    => $comments,
            'timeExecute' => $timeExecute,
            'welcomeText' => $welcomeText,
            'cloud'       => $cloud['cloud'],
            'cloudStyle'  => $cloud['cloudStyle'],
            'filtersOpen' => isset($search['filter_open']) ? $search['filter_open'] : false,
            'colChains'   => $collectiveChains->getResult(),
            'banners'     => $dynamicBanners,
            'topicsArray' => $topicsArray,
            'userFriends' => $userFriend
        ]);

        $time = time() + (3600 * 24 * 7);

        if ((!$request->cookies->get('modal')) && !$search) {
            $response->headers->setCookie(new Cookie('modal', true, $time));
        }

        if (($pagination->getTotalItemCount() > 0) && $search && (!$request->cookies->get('comment_modal')) && ($request->cookies->get('modal'))) {
            $response->headers->setCookie(new Cookie('comment_modal', true, $time));
        }

        if ($pagination->getTotalItemCount() == 0 && (!$request->cookies->get('add_thought_modal')) && ($request->cookies->get('modal'))) {
            $response->headers->setCookie(new Cookie('add_thought_modal', true, $time));
        }

        return $response;
    }

    /**
     * @Route("/link-quotes", name="link-quotes", options={"expose"=true})
     * @param Request $request
     */
    public function linkQuotes(Request $request)
    {
        $em = $this->getDoctrine()->getEntityManager();
        $thoughtId = $request->get('thought_id');
        $thoughtRelatedId = $request->get('thoughtRelated_id');
        $user = $this->getUser();
        $thought = $em->getRepository(Thought::class)->find($thoughtId);
        $thoughtR = $em->getRepository(Thought::class)->find($thoughtRelatedId);

        if (!$thought or !$thoughtR) {
            return new JsonResponse([
                'success' => false,
                'message' => 'There is no such quote found',
            ]);
        }

        if ($em->getRepository(ThoughtRelated::class)->findOneBy(['owner' => $user ,'thought' => $thoughtId, 'relatedThought' => $thoughtR])) {
            return new JsonResponse([
                'success' => false,
                'message' => 'This related already exists.',
            ]);
        }

        if ($user) {
            $thoughtRelated = new ThoughtRelated();
            $thoughtRelated->setThought($thought);
            $thoughtRelated->setRelatedThought($thoughtR);
            $thoughtRelated->setOwner($user);
            $em->persist($thoughtRelated);
            $em->flush();
        }

        return new JsonResponse([
            'success' => true,
            'message' => 'The quote was successfully linked',
        ]);
    }

    public function bannerAction(Banner $banner)
    {
        return $this->render('@Thought/include/banner.html.twig', [
            'banner' => $banner,
        ]);
    }

    /**
     * @param int     $thoughtId
     * @param Request $request
     *
     * @return JsonResponse
     *
     * @throws OptimisticLockException
     * @Route("/thought-likes/{thoughtId}", name="thought-like", requirements={"offerId" = "\d+"}, options={"expose"=true})
     */
    public function likeAction($thoughtId, Request $request)
    {
        $em = $this->getDoctrine()->getManager();

        $modelThought              = $this->container->get('thought.model.thought_model');
        $recommendedThoughtService = $this->container->get('thought.recommended_thought');
        /** @var Thought $thought */
        $thought = $em->getRepository('ThoughtBundle:Thought')->find($thoughtId);

        $result = 'add';

        if (!$thought) {
            return new JsonResponse([
                'success' => false,
                'message' => 'Quote not found',
            ]);
        }
        /** @var Like[] $likes */
        $likes = $thought->getLikes();

        if (isset($likes)) {
            foreach ($likes as $like) {
                if ($like->getUser() === $this->getUser()) {
                    $ourLike = $like;
                }
            }
        }

        if (isset($ourLike)) {
            $thought = $modelThought->removeLike($thought, $this->getUser());
            $result  = 'remove';
        } else {
            $thought = $modelThought->addLike($thought, $this->getUser());
            $recommendedThoughtService->addWatchedThought($this->getUser(), $thought);
        }

        return new JsonResponse([
            'result' => $result,
            'count'  => count($thought->getLikes()),
        ]);
    }
}
